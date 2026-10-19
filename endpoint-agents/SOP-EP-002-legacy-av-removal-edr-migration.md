# SOP-EP-002 · Removing a legacy antivirus agent before EDR migration

Remove a legacy antivirus agent cleanly, prove the endpoint is clean, and hand over to the new EDR without ever running two real-time engines and without leaving the machine unprotected longer than necessary. Trend Micro (Apex One / OfficeScan) is the worked example; the new EDR is Microsoft Defender for Endpoint or CylancePROTECT.

**Family:** Endpoint agents · **Covers:** why engines conflict, uninstall passwords and the SCUT removal tool, the two sequencing models, removal through Programs and Features, SCUT, the vendor console or scripted mass removal (ConfigMgr, Intune), the six clean checks and EDR hand-over · **Does not cover:** configuring the new EDR after onboarding.

## Flow

![Six steps, prepare, remove, reboot, verify clean, install EDR and confirm, with the legacy AV active until the reboot, Defender Antivirus covering the gap and the new EDR active at the end; model A removes then installs, model B overlaps Defender for Endpoint in passive mode so there is no gap](diagrams/sop-ep-002-1.svg)

Real-time protection inserts a file-system minifilter driver into the Windows I/O path. Two engines both intercept every file operation: double scanning, deadlocks, each quarantining the other, blue screens. Defender Antivirus steps aside when another AV registers with Windows Security Center and turns itself back on when that AV is removed, so it covers the gap.

| Model | How it works | Use when |
|---|---|---|
| A · Remove, then install | Uninstall, reboot, verify, install the new EDR; Defender Antivirus covers the gap | Third-party EDR, for example CylancePROTECT, that needs a clean machine |
| B · Overlap, then remove | Onboard Defender for Endpoint in passive mode with mutual exclusions, remove the legacy AV, MDE goes active | Migrating to Defender for Endpoint per Microsoft's guidance; no gap |

![Decision tree: a few PCs with a known password and healthy agent use Programs and Features, broken agents use SCUT; many PCs use scripted removal if managed by ConfigMgr or Intune, otherwise the vendor console; every method ends with six clean checks before the new EDR](diagrams/sop-ep-002-2.svg)

## Before you start

| Item | Requirement |
|---|---|
| Access | Local Administrators (dedicated or LAPS account, elevated prompt for SCUT); vault read for the uninstall password, or AV console admin; AV console role with uninstall rights (Method C); ConfigMgr Application Author and Deployment Manager, or Intune Application Manager or Remediations role; new EDR console role. Activate roles through PIM alongside the vault check-out |
| Licensing | Intune Remediations need Windows Enterprise E3/E5 or equivalent |
| Change | Approved change (for example `CHG0012345`) with the endpoint list and sequencing model; security operations or CAB approves the gap |
| Files | Current SCUT for the installed agent version (for example `SCUT_<release>.zip`), hash recorded; new EDR installer, token or onboarding package; certificate bundle (`.p7b`) |
| Uninstall password | Stored in the privileged-access vault, given only to the migration team, each use logged against the change, rotated afterwards |
| Endpoints | Security Center lists the legacy AV; users warned of a reboot; laptops on AC power and the network or VPN |
| Pilot | 5–20 endpoints across hardware models before fleet roll-out |
| Risk | Medium: a temporary protection gap |

```powershell
Get-CimInstance -Namespace root/SecurityCenter2 -ClassName AntiVirusProduct |
  Select displayName, productState, pathToSignedReportingExe
Get-Service | Where-Object { $_.Name -match '^Tm|ntrtscan|TMBMServer' -or $_.DisplayName -match 'Trend Micro|Apex One|OfficeScan' }
fltmc filters                                   # note the tm* minifilters
Get-MpComputerStatus | Select AMRunningMode, AntivirusEnabled, RealTimeProtectionEnabled
```

## Steps

### Interactive removal

1. **Method A · Programs and Features.** With your admin account open **Settings › Apps › Installed apps** (or `appwiz.cpl`), select the Trend Micro security agent, **Uninstall**, enter the uninstall password from the vault. Reboot when prompted; drivers unload only at restart. An unload password only stops protection until the next boot; it is not removal.
2. **Method B · SCUT.** Copy the ZIP to `C:\Install\SCUT\` (not a user profile), verify its hash, **Extract All**. Open **Command Prompt › Run as administrator**. Run the tool and do not close the window early; expect `Finished StepN` lines and a final cleanup message. Reboot, and keep the debug log with the change record.

```bat
cd /d C:\Install\SCUT
SCUT.exe -noinstall -dbg
shutdown /r /t 60 /c "Restart to complete legacy AV removal"
```

`-noinstall` removes the agent without reinstalling; `-dbg` writes the debug log needed as evidence and for vendor support.

### Console and mass removal

3. **Method C · vendor console.** In the Trend Micro console select the targets or a pilot group and run the **Uninstall** task (menu path varies across Apex One on-premises, SaaS and OfficeScan). No password is needed; offline endpoints act when they reconnect. Damaged or disconnected agents never get the task: catch them with B or D.
4. **Method D · scripted removal.** `Remove-LegacyAV.ps1` runs as SYSTEM, records the Trend footprint (services, processes, programs, registry), exits 0 if already clean, runs SCUT with `-noinstall -dbg`, re-checks, writes transcript and JSON evidence, and exits 0 clean, 3010 clean after reboot, 1 failed.
5. **Deploy it.** ConfigMgr: application running `powershell.exe -ExecutionPolicy Bypass -File Remove-LegacyAV.ps1`, script detection that reports installed when no footprint remains, 3010 mapped to soft reboot, Required to the pilot collection. Intune Win32: same package via `IntuneWinAppUtil.exe`, install behaviour System, custom detection script. Intune Remediations: detection exits 1 when a footprint exists, remediation runs the removal; status in **Devices › Scripts and remediations**. Pilot first: some agent versions demand the password even from SYSTEM.

```powershell
$left = Get-Service | Where-Object { $_.Name -match '^Tm|ntrtscan|TMBMServer' -or $_.DisplayName -match 'Trend Micro' }
$reg  = (Test-Path 'HKLM:\SOFTWARE\TrendMicro') -or (Test-Path 'HKLM:\SOFTWARE\WOW6432Node\TrendMicro')
if (-not $left -and -not $reg) { Write-Output 'Legacy AV removed' }   # output + exit 0 = "installed", i.e. clean
exit 0
```

### Hand-over

6. **Prove clean.** After the reboot run `Test-LegacyAVRemoved.ps1` elevated. "The uninstaller finished" is not evidence; every check must pass.
7. **Certificates first.** Import the bundle, for example `Import-Certificate -FilePath C:\Install\EDR\vendor-chain.p7b -CertStoreLocation Cert:\LocalMachine\Root` (CA for intermediates, TrustedPublisher for code-signing, as instructed). At scale use an Intune Trusted certificate profile or Group Policy. This prevents an install that succeeds but never registers.
8. **Install the EDR.** CylancePROTECT: vendor MSI with the console token, for example `msiexec /i CylancePROTECT_x64.msi /qn PIDKEY=<install-token>`. Defender for Endpoint: onboarding package, or Intune **Endpoint security › Endpoint detection and response**.
9. **Close the gap.** Record the time between removal and confirmed protection in the change record.

## Verify

| Check | Pass |
|---|---|
| Services | No `Tm*`, `ntrtscan`, `TMBMServer` |
| Processes | No `PccNTMon`, `Tm*`, `NTRtScan` |
| Drivers | `fltmc filters` shows no `tm*` filter |
| Registry | No `HKLM\SOFTWARE\TrendMicro` (or WOW6432Node) |
| Programs and folders | No Trend Micro entry; Trend Micro program folder gone (an empty log-only folder is harmless, record it) |
| Security Center | `root/SecurityCenter2` no longer lists the legacy AV |
| During the gap | `Get-MpComputerStatus`: AMRunningMode Normal, real-time protection on |
| New EDR | Healthy locally and online in its console; listed in Security Center; EICAR test file detected |

## Rollback

If the new EDR cannot be installed, do not leave the endpoint on Defender by accident: either keep Defender Antivirus as a documented interim control, or reinstall the legacy agent from its console package and re-register it until the blocker is fixed. Record which state the endpoint is in.

## Troubleshooting

Rule out elevation, remnants and locked services in order; escalate to the vendor only with the `-dbg` logs.

| Symptom | Cause and fix |
|---|---|
| Tool fails to launch | Not elevated: reopen Command Prompt with **Run as administrator** |
| Agent still in Programs | Removal incomplete: re-run the tool, reboot, check the TrendMicro registry keys |
| Services still active after reboot | Self-protection driver still loaded: boot into Safe Mode, run the tool again, reboot normally |
| Password nobody knows | Retrieve it from the console policy, use Method C, or use SCUT |
| `fltmc` still lists `tm*` | Driver not removed: reboot; if it persists, send the debug log to vendor support. Never delete driver files by hand |
| New EDR fails or never registers | Remnants, missing certificate or proxy blocking the EDR cloud: re-verify, import certificates, test connectivity |
| Defender stays off | A policy still disables it, or Security Center lists a stale product: check policies and `Get-MpComputerStatus` |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | SI-3 Malicious code protection | Endpoint is never left without an active engine; the gap is covered by Defender and timed |
| | CM-3 Configuration change control | Removal runs under an approved change, piloted first, with before and after evidence |
| | AC-6, IA-5 | Uninstall password vaulted, issued to the migration team only, logged per use and rotated |
| | AU-12 Audit record generation | Transcripts, JSON footprints and SCUT debug logs per endpoint against the change reference |
