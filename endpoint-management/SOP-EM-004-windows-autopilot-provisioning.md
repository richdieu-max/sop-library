# SOP-EM-004 · Provisioning Windows devices with Windows Autopilot and Intune

Turn the Windows installation a laptop ships with into a managed, compliant corporate device the first time it is switched on. Register the hardware hash, target the device with a dynamic group, build the deployment profile and Enrollment Status Page, and hand a sealed laptop to a user who signs in once. Nothing is imaged.

**Family:** Endpoint management · **Covers:** registration (OEM, CSV, `Get-WindowsAutopilotInfo`), ZTDId dynamic groups, the deployment profile and ESP, user-driven, pre-provisioned and self-deploying modes, Graph bulk work, reset and deregistration · **Does not cover:** hybrid join build-out, or the update rings and wipe approvals themselves (SOP-EM-005, SOP-EM-003).

## Flow

![Before shipping, the OEM, a CSV import or the script creates the Autopilot record, a dynamic group matches its ZTDId and carries the profile and ESP; at first boot the device downloads its profile, the user signs in, the device joins Entra ID and enrolls, and the ESP holds the desktop until it is ready](diagrams/sop-em-004-1.svg)

The hardware hash creates a Windows Autopilot device record, which stamps the Entra device object with `[ZTDId]:<guid>` and an optional group tag `[OrderID]:<tag>`. The profile is fetched at the network step of OOBE, so a device registered after first boot needs a reset or reboot back to OOBE.

| Mode | Who is present | Notes |
|---|---|---|
| User-driven (default) | The user | 30–90 minutes, works from home |
| Pre-provisioned | IT or reseller runs device phases (Win key ×5), user finishes | User phase 10–20 minutes; TPM 2.0 attestation, physical device |
| Self-deploying | No user | Kiosks, shared PCs; TPM 2.0 attestation; target everything at the device |
| Autopilot device preparation | The user | No hash; static device group; Entra join and Windows 11 only. A classic profile takes precedence |

Entra join is the standard. Hybrid join needs the Intune Connector for AD and domain controller line of sight during OOBE, and is a documented exception only.

## Before you start

| Item | Requirement |
|---|---|
| Roles | Intune Administrator or Policy and Profile Manager through PIM; Groups Administrator for dynamic groups; Organizational Branding Administrator; Help Desk Operator for reset |
| Licensing | Intune and Entra ID P1 per user (M365 E3/E5, Business Premium, EMS E3/E5); Windows 10/11 Pro, Business, Enterprise or Education |
| Tenant settings | **Devices › Enrollment › Windows › Automatic Enrollment**: MDM user scope All; Entra **Device settings**: users may join devices; Windows (MDM) allowed in enrollment restrictions; company branding set |
| Network | Autopilot, Entra ID, Intune, Windows Update, Delivery Optimization and TPM attestation endpoints, no TLS inspection |
| Policies on the device group | Compliance, BitLocker, Defender onboarding, Windows Hello for Business, update ring (SOP-EM-005), LAPS, security baseline |
| Procurement | OEM or reseller registers hashes against every order with the tenant ID and group tag |
| Decisions | Group tags `STD`, `EXEC`, `LAB`, `KIOSK`; name template `CTS-%SERIAL%` (15 characters maximum); Standard user accounts |
| Risk | Low for new devices; moderate for ESP blocking-list changes and reset; high for wipe, delete and deregister |

## Steps

### Register

1. **Collect a hash on a device in hand.** At the first OOBE screen press **Shift+F10**, start PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned -Force
Install-Script -Name Get-WindowsAutopilotInfo -Force
Get-WindowsAutopilotInfo -Online -GroupTag "STD" -Assign   # uploads via Graph
# or export: Get-WindowsAutopilotInfo -OutputFile C:\HWID\$env:COMPUTERNAME.csv
```

2. **Import a CSV.** **Devices › Enrollment › Windows › Devices** (Windows Autopilot) › **Import**. Keep the header exactly as exported, no Excel re-save, no more than 500 rows. **Sync** and **Refresh**; each serial shows Profile status Not assigned until the group and profile exist. Correct a group tag on the record rather than re-importing.
3. **Dynamic group.** Entra admin center › **Groups › All groups › New group**: Security, `Autopilot-STD`, **Dynamic Device**, rule `(device.devicePhysicalIds -any (_ -eq "[OrderID]:STD"))`. `Autopilot-All` uses `(device.devicePhysicalIDs -any (_ -startsWith "[ZTDid]"))`. **Validate Rules** against one known device and wait for membership.

### Build

4. **Deployment profile.** **Devices › Enrollment › Windows › Deployment profiles › Create profile › Windows PC**, `AP-UserDriven-STD`. Convert all targeted devices No (use it only in its own profile for an existing fleet). User-Driven, Microsoft Entra joined; hide licence terms, privacy settings and change-account options; account type Standard; allow pre-provisioned deployment Yes; name template `CTS-%SERIAL%`. Assign to `Autopilot-STD`.
5. **Enrollment Status Page.** **Devices › Enrollment › Windows › Enrollment Status Page › Create**, `ESP-STD`. Show progress Yes, error after 60 minutes, custom message with the service desk number, log collection Yes, only OOBE devices Yes, block until installed Yes, allow reset on error Yes, allow use on error No. Block only on selected apps: Company Portal, Defender configuration, VPN client, one core LOB app. Assign to `Autopilot-STD`. Every blocking app is a single point of failure, and Win32 and legacy MSI installs can collide during ESP.

### Deploy

6. **User-driven.** The user picks region and network, signs in on the branded page with MFA, the device joins and enrolls, device and account setup run, Windows Hello for Business is set up, the desktop appears.
7. **Pre-provisioned.** Technician presses **Win key ×5** at the first OOBE screen, chooses **Pre-provision with Windows Autopilot**, confirms profile and tag, lets device phases run. Green screen: **Reseal** and ship. Red screen: view diagnostics, reset.
8. **Self-deploying.** Assign a Self-Deploying profile to `Autopilot-KIOSK`, paired with a kiosk (Assigned Access) or shared multi-user profile.

### At scale (Graph)

9. **Bulk import and report.** Connect with `DeviceManagementServiceConfig.ReadWrite.All`, `DeviceManagementManagedDevices.Read.All` and `Group.Read.All`. POST each CSV row to `importedWindowsAutopilotDeviceIdentities`, call `windowsAutopilotSettings/sync`, then list `windowsAutopilotDeviceIdentities` where `deploymentProfileAssignmentStatus` is not assigned. The community WindowsAutopilotIntune module wraps the same endpoints; pin and review the version in a regulated environment.

## Verify

| Check | Pass |
|---|---|
| Windows Autopilot devices | Serial present, group tag correct, Profile status Assigned |
| Entra ID › device › Groups | Member of `Autopilot-All` and its persona group |
| **Devices › Monitor › Autopilot deployments** | Status Success; deployment and ESP durations recorded |
| `dsregcmd /status` | `AzureAdJoined : YES`; MDM URL present |
| Intune device | BitLocker on, Defender onboarded, compliant, named `CTS-<serial>` |
| Test sign-in | Standard user; Windows Hello set up; required apps installed |

## Rollback

| Action | Effect | Use |
|---|---|---|
| Autopilot Reset | Removes user files, apps and settings; keeps join, enrollment and Wi-Fi | New user, same role |
| Wipe | Factory reset; re-runs Autopilot, registration survives | Rebuild, malware, persona change |
| Delete Intune record, then deregister | Device no longer finds its profile | Disposal, return, tenant move |

Delete the Intune device before the Autopilot record; an enrolled device cannot be deregistered. Record serial and reason in the asset register. Wipes on high-value devices may need a second admin's approval (SOP-EM-003).

## Troubleshooting

Read the code and phase on screen, then collect diagnostics once, before resetting: a reset discards the evidence.

```powershell
MdmDiagnosticsTool.exe -area "Autopilot;DeviceEnrollment;DeviceProvisioning;TPM" -cab C:\Diag\autopilot.cab
dsregcmd /status
Get-WinEvent -LogName "Microsoft-Windows-ModernDeployment-Diagnostics-Provider/Autopilot" -MaxEvents 50
```

| Symptom | Cause and fix |
|---|---|
| Consumer OOBE, no company page | Profile not assigned, device not in group or no network at the profile step: fix the group, wipe back to OOBE |
| 0x80180014 | Windows MDM blocked by restrictions or a stale Intune record: allow Windows (MDM), delete the record |
| 0x800705b4 ESP time-out | Blocking app failed or slow, or Win32/MSI collision: check the IME log in `C:\ProgramData\Microsoft\IntuneManagementExtension\Logs`, fix or remove the app, raise the time-out only after |
| 0x801c03ea pre-provisioning red screen | TPM not 2.0, firmware issue or attestation blocked: update BIOS/TPM, clear TPM, use user-driven |
| 0x80180018 | User has no Intune licence: assign and retry |
| 0x801c0003 | User not allowed to join devices: fix Entra device settings |
| Import error 806 / 808 | Already registered in this tenant (806) or another tenant, which must deregister it (808) |
| Name not applied | Template invalid, over 15 characters, or hybrid join |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | CM-2, CM-6 | Every device built to the same profile, ESP and policy baseline |
| | CM-8, IA-3 | Hardware hash and serial identify each device in the Autopilot and Intune records |
| | SC-28 | BitLocker lands during the device phase, before user data exists |
| CIS Controls v8 | 1.1, 4.1, 4.7 | Asset inventory, secure configuration process, standard user and LAPS instead of shared local admin |
| FDA 21 CFR Part 11 / GAMP 5 | Computerized-system clients | Documented, repeatable build with configuration evidence per device |
