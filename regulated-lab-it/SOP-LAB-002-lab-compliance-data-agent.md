# SOP-LAB-002 · Installing, registering and patching a lab compliance data agent

Register a lab workstation, install and connect a GxP data-capture agent, and apply a vendor hotfix under change control, with evidence for the record. The agent records every create, change, rename and delete of instrument result files with who and when, and sends it to the server that keeps the audit trail; if it is missing, stopped or cut off, records pile up unattested.

**Family:** Regulated lab IT · **Covers:** console registration, four install methods (interactive; silent msiexec and PowerShell; remote via BeyondTrust PRA or PowerShell remoting; ConfigMgr or Intune Win32), the hotfix lifecycle, verification, rollback · **Does not cover:** server installation. Compliance Builder is the worked example; the pattern applies to any agent paired with a central server.

## Shape

![Instrument writes result files; the workstation agent captures events, queues them locally during outages and uploads them over TLS through a firewall that allows only the agent port to the compliance server, which stores the audit trail and e-signatures; admins and reviewers use the web console over HTTPS](diagrams/sop-lab-002-1.svg)

Registration ties the workstation's hostname to a **System** (for example *Mechanical Test Lab · Tensile testers*), and the System supplies the capture rules. Most products refuse or quarantine agents from unregistered workstations, which is why every method starts in the console.

## Before you start

| Item | Requirement |
|---|---|
| Change | Approved change record (for example `CHG0012345`) and a window agreed with the lab, because instrument runs must be paused |
| Packages | Approved `CBAgentSetup.msi` and hotfix from the controlled repository, with vendor checksums |
| Access | Web console role that can add Workstations; Local Administrators via a separate or LAPS-managed admin account, never the analyst's; just-in-time elevation where available (the activation log is evidence) |
| Service identity | Vendor default (often LocalSystem) if the agent only reads local folders; gMSA if it must reach network shares and the vendor supports it; otherwise a dedicated domain account with **Log on as a service** only, interactive and RDP logon denied. Never shared, never known to analysts |
| Network | Server `<cb-server.contoso.com>`, port `<agent-port>`, direction of each connection and TLS confirmed with the vendor and server owner; lab VLAN ACL change requested before the day |
| Time | Clock synchronized with the domain (`w32tm /query /status`): audit-trail timestamps depend on it |
| Method D access | ConfigMgr Application Author / Application Deployment Manager scoped to the lab collection, or Intune Application Manager with scope tag Lab |
| Re-validation | Ask Quality whether the hotfix needs executed OQ scripts on each workstation or on a representative one |

Choosing a method: 1–3 PCs with hands on the keyboard use **A**; 1–3 remote use **C**; fleets on ConfigMgr or Intune use **D**; scripted batches otherwise use **B**. Remote sessions usually run the Method B commands anyway.

## Steps

### Register (every method)

1. **Console first.** Sign in to the web console; under **Systems** record the target System's name and server/port. Under **Workstations › Add** enter the hostname exactly as Windows reports it (`hostname`) plus System, lab, owner and purpose. Save, run a **System Reload** if your environment needs it, and screenshot the entry. Hostname mismatches (typo, old name after reimage, NetBIOS differing from DNS) are the most common reason an agent never connects.
2. **Pre-flight.** Before the window, run `Test-AgentPrereqs.ps1` on the workstation: admin rights, time source, DNS resolution, `Test-NetConnection` to the port, free disk and pending reboot.

### Method A · Interactive

3. **Install.** Copy the MSI to `C:\Install\CBAgent\`, check `Get-FileHash .\CBAgentSetup.msi -Algorithm SHA256` against the repository, and run `msiexec /i CBAgentSetup.msi` from an elevated prompt. Supply the service account if prompted.
4. **Connect.** In the **Agent Configuration Utility › Connections**, add the entry for the System (server, port, authentication). In `services.msc` set the agent to **Automatic** and restart it. Confirm **Connections** is healthy in the agent window and the workstation reports in the console under the right System. If correct configuration still shows disconnected, one clean reboot, recorded, often fixes it.

### Method B · Silent

5. **Run the template.** `Install-ComplianceAgent.ps1` verifies the checksum, installs silently with a verbose log, sets the service identity, Automatic start and restart-on-failure, optionally applies the hotfix with the service stopped, then writes a JSON evidence file. Run it with `-WhatIf` first:

```powershell
$hash = (Get-FileHash $MsiPath -Algorithm SHA256).Hash
if ($hash -ne $ExpectedSha256) { throw "Checksum mismatch: $hash" }
$p = Start-Process msiexec.exe -Wait -PassThru -ArgumentList "/i `"$MsiPath`" /qn /norestart /l*v `"$log`" $MsiProperties"
if ($p.ExitCode -notin 0,3010) { throw "msiexec exit $($p.ExitCode). See $log" }
Set-Service -Name $ServiceName -StartupType Automatic
sc.exe failure $ServiceName reset= 86400 actions= restart/60000/restart/60000// | Out-Null
```

   Whether server and port are public MSI properties, and their names, is product-specific: read the Property table in Orca or via `msiexec /a`. Exit 0 is success, 3010 is success with reboot.
6. **Firewall, only if the server calls back.** An inbound rule scoped to the server address and the Domain profile, delivered by Group Policy or an Intune firewall rules policy (**Endpoint security › Firewall**) so it cannot drift.

### Method C · Remote

7. **BeyondTrust PRA.** Open the workstation's Jump Item (or send a session invite), confirm hostname and OS, copy files with **File Transfer**, then run Method A on **Screen Sharing** or Method B in the elevated **Command Shell**. Never take over a screen while an instrument is acquiring. The session recording is evidence.
8. **PowerShell remoting.** From a jump host, `New-PSSession`, copy the MSI and script with `Copy-Item -ToSession` (a UNC path inside the session fails on the Kerberos double hop), run the template with `Invoke-Command`, and copy the evidence back with `-FromSession`.

### Method D · Enterprise

9. **ConfigMgr.** **Software Library › Application Management › Applications › Create Application** from the MSI; set the silent command line, keep MSI product-code detection, install for system whether or not a user is logged on, handle 3010. Model the hotfix as a superseding application; deploy Required to the lab device collection so its maintenance window applies; export the success list from **Monitoring › Deployments**.
10. **Intune Win32.** Wrap with `IntuneWinAppUtil.exe -c .\src -s install.cmd -o .\out`; **Apps › Windows › + Add › Windows app (Win32)**; uninstall `msiexec /x {<ProductCode>} /qn`; detection by product code (with version for the hotfix); Required to a lab device group with a scope tag; supersedence for the hotfix. Intune has no maintenance window for Win32 apps: use a deadline time, deploy as Available and install in the window, or keep validated PCs on ConfigMgr.

### Hotfix

11. **Assess and test.** Read the release notes with Quality or the CSV lead: does it touch data capture, signatures or audit trail; must server and agent versions match; do existing OQ scripts cover it? Pass it on a test system, then get the change approved and the window booked.
12. **Deploy.** Confirm the package checksum; confirm the agent queue is empty and the console's last contact is current; stop the service if the vendor requires; run the hotfix (`msiexec /p` for an .msp); start the service; confirm Connections, console visibility and the new version. In a test batch, create a file in a monitored folder, watch the event arrive and sign it with a test account.

## Verify

| Check | Pass |
|---|---|
| Service | Running, Automatic, recovery actions set, expected account |
| Agent | Connections tab healthy; agent and hotfix versions as approved |
| Console | Workstation listed under the correct System and lab; last-contact time current; test event received and signed |
| Installer | No MsiInstaller errors in the Application log for the window |
| Time | `w32tm /query /status` shows the domain source |
| Evidence | Change ID and window; versions before and after; hotfix ID and checksum; screenshots of Connections and console; hostname, OS, operator and UTC time; msiexec logs, JSON file, PRA recording |

## Rollback

Stop the service. Remove the hotfix per vendor guidance (for an MSP marked uninstallable: `msiexec /package {<ProductCode>} MSIPATCHREMOVE={<PatchCode>} /qn`). If needed, `msiexec /x {<ProductCode>} /qn /norestart`, reboot and install the known-good version. Re-add the connection, validate as above, and record the rollback and reason; open a problem record if the vendor must investigate.

## Troubleshooting

Work outward from the PC: service running, connection entry present, port reachable, then registration. Reinstalling is the last resort. **Never delete the agent's local queue or database to clear an error**: it destroys unsent audit-trail events, which is a data-integrity incident. Escalate to the system owner and vendor.

| Symptom | Cause and fix |
|---|---|
| Installed but never connects | No connection entry: add it in the Agent Configuration Utility, save, restart the service |
| Connection entry exists, still red | Not registered or server not reloaded: add under Workstations, System Reload |
| `TcpTestSucceeded : False` | Firewall or VLAN ACL: network request listing source, destination and `<agent-port>` |
| Service starts then stops (Event ID 7034/7031) | Service account password expired or lacks Log on as a service, or corrupt config: check the System log and vendor log folder |
| Wrong event timestamps | Time not synchronized: `w32tm /resync`, then check the domain hierarchy |
| msiexec 1603 | Search the verbose log for "Return value 3": often a pending reboot or files locked by a running agent |
| Remote session lost after reboot | Fresh PRA invite after sign-in, or wait for the Jump Client |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| FDA 21 CFR Part 11 | §11.10(a) validation; §11.10(e) audit trails | Hotfix tested and approved before production; the agent feeds the computer-generated audit trail |
| | Attributability | Named admin accounts, a dedicated non-interactive service account and recorded PRA sessions |
| EU GMP Annex 11 | §10 change and configuration management | Install and hotfix run as controlled changes with rollback |
| ALCOA+ | Data integrity | Evidence items map to Attributable, Contemporaneous, Original, Accurate, Complete, Enduring and Available; time sync protects every timestamp |
