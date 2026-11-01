import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("At scale: Intune Win32, ConfigMgr, GPO startup script or the Tanium-native route",
            "Prefer the platform that already manages the endpoint; the native deployment is for estates nothing manages yet, and remoting is for a handful.",
            height=828)

# ---------------- decision ladder
d.zone(32, 100, 1216, 190, "Which route? Ask about the endpoint, not the agent", icon="question-diamond-gold")
qs = [("Already managed by Intune?", "D", "Intune Win32 app", C.blue),
      ("Managed by ConfigMgr?", "D", "ConfigMgr application", C.blue),
      ("Domain-joined, neither?", "D", "GPO startup script", C.blue),
      ("Unmanaged estate, M&A?", "E", "Tanium client deployment", C.purple),
      ("Just a handful of PCs?", "C", "PsExec or WinRM", C.grey)]
for i, (q, letter, route, col) in enumerate(qs):
    x = 48 + i * 240
    d.card(x, 140, 224, 54, "", [], accent=C.gold, shadow=False)
    d.text(x + 14, y := 162, q, 12, 600, C.ink, max_w=200)
    d.text(x + 14, 180, "yes ↓", 10.5, 400, C.grey)
    d.arrow([(x + 112, 194), (x + 112, 214)], col)
    d.card(x, 216, 224, 56, route, [], badge=letter, badge_color=col, accent=col, shadow=False, title_size=12.5)
    if i < 4:
        d.text(x + 232, 170, "no →", 10.5, 400, C.grey, "middle")

# ---------------- comparison matrix
d.zone(32, 306, 1216, 338, "The four fleet routes compared", icon="server-stack", note="all run SetupClient.exe /S with tanium-init.dat beside it")
cols = [240, 232, 232, 232, 232]
hdr = ["", "Intune Win32", "ConfigMgr", "GPO startup script", "Tanium client deployment"]
rows = [
    ["Package", "source folder + install.cmd (%~dp0), IntuneWinAppUtil", "both files on the content share, Script Installer", "idempotent script on a read-only share", "targets plus a stored deployment credential"],
    ["Runs as", "System, Required to a device group", "system, whether or not a user is logged on", "computer startup, before any user", "console credential over SMB 445"],
    ["Detection", "TaniumClient.exe or the service", "file detection rule", "returns early if the service exists", "per-endpoint results in the console"],
    ["Reporting", "app install status", "Monitoring › Deployments", "none: query for stragglers", "per endpoint; discovery finds unmanaged PCs"],
    ["Uninstall", "uninst.exe /S (confirm the path)", "uninstall deployment", "not provided by the script", "not provided"],
    ["Role needed", "Intune Application Manager", "Application Author + Deployment Manager", "GPO edit and OU link rights", "a Tanium role to deploy clients"],
    ["Afterwards", "nothing extra", "nothing extra", "remove the link once complete", "remove the credential's rights or rotate it"],
]
y = 346
x0 = 48
# header
d.rect(x0, y, sum(cols), 28, fill=C.zone, stroke=C.border, rx=0)
cx = x0
for ci, h in enumerate(hdr):
    if h:
        d.text(cx + 8, y + 19, h, 12, 600, C.ink)
    cx += cols[ci]
y += 28
for ri, row in enumerate(rows):
    rh = 36
    d.rect(x0, y, sum(cols), rh, fill="#fff" if ri % 2 else "#FCFCFB", stroke=C.rule, rx=0)
    cx = x0
    for ci, cell in enumerate(row):
        if ci == 0:
            d.text(cx + 8, y + 22, cell, 12, 600, C.ink)
        else:
            d.lines(cx + 8, y + 16, cell, 10.5, cols[ci] - (100 if row[0] == "Reporting" else 16), 400, C.grey, lh=13)
        cx += cols[ci]
    y += rh
# reporting pills overlay on the Reporting row
rep_y = 346 + 28 + 3 * 36
for ci, (label, col) in enumerate([("yes", C.green), ("yes", C.green), ("no", C.red), ("yes", C.green)]):
    d.pill(x0 + cols[0] + sum(cols[1:ci + 1]) + cols[ci + 1] - 56, rep_y + 8, label, col)

# ---------------- bottom: the handful route and the common rules
d.zone(32, 660, 600, 100, "Route C for a handful: PsExec or PowerShell remoting", icon="terminal")
d.lines(48, 706, "psexec \\\\PC -s -w C:\\Install\\Tanium SetupClient.exe /S, or Copy-Item -ToSession and Invoke-Command with the template. Many EDR products flag PsExec: tell security operations first, or use remoting.", 11, 568, 400, C.grey, lh=15)
d.zone(656, 660, 592, 100, "Every route, every time", icon="checklist-purple")
d.lines(672, 706, "Just-in-time roles only. SHA-256 of both files checked. Never reuse an init file from another environment. Notify the tooling owner and have them confirm the endpoint reports.", 11, 560, 400, C.grey, lh=15)

d.note_bottom("Method letters match the runbook's method table: C remote, D managed fleets, E Tanium-native. Controls: CM-8 (inventory), AC-6 (scoped, just-in-time roles; credential rights removed after the campaign).")
d.render(repo_path("endpoint-agents/diagrams/sop-ep-001-3.svg"))
