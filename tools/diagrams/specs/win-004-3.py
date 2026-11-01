import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path, text_width

d = Diagram("The same job in CMD, PowerShell, over WinRM and through Intune, by risk class",
            "Each task family has a local text form, a local object form, a remote form and a fleet form; the verb sets the risk class and the precaution, wherever it runs.",
            height=884)

cols = [("Task family", 150), ("A · CMD (text)", 240), ("B · PowerShell (objects)", 288), ("C · Remote (WinRM)", 220), ("D · Intune (fleet)", 196), ("Risk", 122)]
x0, y0, rh = 32, 100, 46
# header
cx = x0
d.parts.append(f'<rect x="{x0}" y="{y0}" width="1216" height="30" fill="{C.zone}" stroke="{C.border}" stroke-width="1"/>')
for name, w in cols:
    d.text(cx + 8, y0 + 20, name, 11.5, 600, C.ink, max_w=w - 14)
    cx += w

SAFE, CHG, DST = ("Safe", C.green), ("Changes", C.gold), ("Destructive", C.red)
rows = [
    ("System information", ["systeminfo · hostname · whoami /all", "fsutil volume diskfree C:"], ["Get-ComputerInfo · Get-Volume C", "$env:COMPUTERNAME · whoami /groups"],
     ["Invoke-Command { Get-CimInstance", "Win32_OperatingSystem } → fleet.csv"], ["Collect diagnostics", "(device action)"], [SAFE]),
    ("Cleanup", ["del /s /q %temp%\\*", "DISM /StartComponentCleanup"], ["Remove-Item \"$env:TEMP\\*\" -Recurse", "Repair-WindowsImage -StartComponentCleanup"],
     ["Get-SupportSnapshot.ps1 -ClearTemp", "honours -WhatIf"], ["Remediation as SYSTEM:", "%TEMP% is C:\\Windows\\Temp"], [CHG]),
    ("Network diagnosis", ["ipconfig /all · ping · nslookup", "tracert · pathping · netstat -ano"], ["Get-NetIPConfiguration -Detailed", "Test-NetConnection host -Port 443"],
     ["snapshot -TestHost intranet", "-TestPort 443"], ["Collect diagnostics", "(device action)"], [SAFE]),
    ("Network reset", ["ipconfig /release && /renew", "netsh int ip reset · winsock reset"], ["Restart-NetAdapter -Name Ethernet", "Clear-DnsClientCache"],
     ["chain on one line and expect", "to reconnect; record static IPs"], ["Sync · Restart", "(device actions)"], [CHG]),
    ("Processes, services", ["tasklist /svc · sc query Spooler", "net stop / net start Spooler"], ["Get-Process · Get-Service", "Restart-Service Spooler"],
     ["sc.exe \\\\PC-LAB-0001 query Spooler", "Invoke-Command { Restart-Service }"], ["Remediation: detect Spooler", "stopped, then fix and report"], [SAFE, CHG]),
    ("Local accounts", ["net user kiosk01 * /add", "net user kiosk01 /delete"], ["New-LocalUser -Password", "(Read-Host -AsSecureString)"],
     ["same cmdlets inside", "Invoke-Command"], ["tracked change; admin", "membership removed after"], [CHG, DST]),
    ("Files and copies", ["robocopy /MIR /L, then /MIR", "rmdir /s /q C:\\path\\folder"], ["Remove-Item C:\\path -Recurse", "-WhatIf first"],
     ["Copy-Item -ToSession", "(no double hop to a share)"], ["platform script", "(one-off PowerShell)"], [SAFE, DST]),
    ("OS and volume repair", ["DISM /CheckHealth · /RestoreHealth", "sfc /scannow · chkdsk C: /scan"], ["Repair-WindowsImage -Online", "Repair-Volume -DriveLetter C -Scan"],
     ["Invoke-Command, long-running;", "/r is hours offline"], ["Collect diagnostics, then", "Restart (device action)"], [SAFE, CHG]),
    ("Policy, logs, restart", ["gpupdate /force · wevtutil qe System", "shutdown /r /t 300 /c \"CHG0012345\""], ["Invoke-GPUpdate · Get-WinEvent", "Restart-Computer -Confirm"],
     ["shutdown /r /m \\\\PC-LAB-0001", "/t 600 /c \"Restart for CHG0012345\""], ["Restart", "(device action)"], [CHG]),
]
yy = y0 + 30
for ri, (fam, a, b, c, dd, risk) in enumerate(rows):
    fill = "#fff" if ri % 2 == 0 else "#FCFCFB"
    d.parts.append(f'<rect x="{x0}" y="{yy}" width="1216" height="{rh}" fill="{fill}" stroke="{C.rule}" stroke-width="1"/>')
    cx = x0
    d.text(cx + 8, yy + 28, fam, 11.5, 600, C.ink, max_w=cols[0][1] - 14)
    cx += cols[0][1]
    for cell, (name, w) in zip((a, b, c, dd), cols[1:5]):
        mono = name.startswith(("A", "B"))
        for li, line in enumerate(cell[:2]):
            d.text(cx + 8, yy + 19 + li * 15, line, 10.5, 400, C.grey if not mono else C.ink, mono=mono, max_w=w - 12)
        cx += w
    px = cx + 8
    for (lab, col) in risk:
        px += d.pill(px, yy + 13, lab, col, size=10) + 4
    yy += rh
table_bottom = yy

# ---------------- same task, four ways
d.zone(32, table_bottom + 18, 1216, 134, "One task, four ways: restart the print spooler", icon="printer", note="A and B need an elevated prompt; C needs WinRM; D needs the device enrolled")
sy = table_bottom + 58
four = [("A · CMD", ["net stop Spooler", "net start Spooler", "(elevated prompt)"], C.blue),
        ("B · PowerShell", ["Restart-Service Spooler", "Get-Service Spooler   # read back", "(elevated prompt)"], C.purple),
        ("C · Remote", ["Invoke-Command -ComputerName PC-LAB-0001", "  { Restart-Service Spooler }", "sc.exe \\\\PC-LAB-0001 query Spooler"], C.teal),
        ("D · Intune Remediation", ["detect: exit 1 if Spooler not running", "fix: stop, clear PRINTERS\\*, start,", "write the status as the last line"], C.green)]
for i, (t, b, col) in enumerate(four):
    x = 48 + i * 300
    d.card(x, sy, 292, 76, t, b, accent=col, shadow=False, title_size=12.5, body_size=10.5, mono_body=True)
    if i < 3:
        d.arrow([(x + 292, sy + 38), (x + 300, sy + 38)], C.grey, sw=1.4)

# ---------------- read it before Enter
ry = table_bottom + 168
d.zone(32, ry, 1216, 108, "Read the line left to right before you press Enter", icon="doc-search", note="CMD rarely previews: run the matching read-only command first")
rules = [("Verb = risk class", "Get- safe · Set-, Restart-, Stop- change state · Remove-, Clear-, Format- destructive", C.gold),
         ("Parameter + value = target", "confirm hostname and whoami before any change", C.blue),
         ("-WhatIf = rehearsal", "robocopy /L is the CMD exception; read the summary counts", C.green),
         ("Paths are the danger", "Remove-Item \"$folder\\*\" with an empty $folder becomes \\*; never type a password", C.red)]
for i, (t, b, col) in enumerate(rules):
    d.card(48 + i * 302, ry + 36, 288, 64, t, [b], accent=col, shadow=False, title_size=12, body_size=10.5)

d.note_bottom("Safe: run freely, paste output in the ticket. Changes: warn the user, know the undo. Destructive: verify the target, preview, back up, change control. Controls: CM-3, AC-6, IA-5, AC-17, AU-3.")
d.render(repo_path("windows-support/diagrams/sop-win-004-3.svg"))
