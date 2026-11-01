import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Choosing the migration tool: Migration Manager, SPMT desktop, SPMT PowerShell or sync",
            "Four ways to move a share, compared on the things that decide the choice: scale, where it runs and which role it needs, evidence, throttling, permissions and delta passes.",
            height=812)

cols = [("A", "Migration Manager", "SharePoint admin center + LAN agent", C.blue, "preferred beyond a handful of folders"),
        ("B", "SPMT desktop", "wizard on a machine near the file server", C.purple, "a handful of folders"),
        ("C", "SPMT PowerShell", "CSV wave plan, scripted", C.teal, "waves with evidence"),
        ("D", "OneDrive sync", "robocopy into a synced folder", C.red, "avoid: contrast only")]
LX, CX0, CW, GAP = 48, 262, 236, 12
xs = [CX0 + i * (CW + GAP) for i in range(4)]

d.zone(32, 100, 1216, 550, "Side by side", icon="arrows-lr", note="every method leaves Preserve file share permissions off")
for (letter, name, where, col, verdict), x in zip(cols, xs):
    d.card(x, 140, CW, 62, name, [where], badge=letter, badge_color=col, accent=col, shadow=False, body_size=11)

rows = [
    ("Scale", ["many folders; bulk task from a CSV or JSON; more agents for more throughput", "one wizard run per share", "one task per CSV row; a whole wave per change", "a few gigabytes, only when every tool is blocked"]),
    ("Role and footprint", ["SharePoint Administrator; 64-bit agent on the LAN, outbound 443 only, no inbound rule", "Site Owner on the destination site; no tenant role", "Site Owner; Windows PowerShell 5.1 on the SPMT machine", "no admin role; the sync client's own identity"]),
    ("Evidence", ["scan log, task history, failure report ZIP (FatalError_R1.csv + item reports)", "failure report per run; Scan only without an agent", "-WhatIf, -ScanOnly and JSON evidence per change number", "none"]),
    ("Throttling", ["summary report; when throttled add agents, split tasks, run off-peak", "report per run; one machine, one queue", "same engine as B, driven from the map file", "throttled, no report, can strand files on the server"]),
    ("What is kept", ["authors and modified dates; access re-expressed as team and channel membership", "authors and dates; hidden items off, .tmp and .lnk excluded", "as B, with the same exclusions set in Register-SPMTMigration", "loses authors and timestamps"]),
    ("Delta pass", ["Run again or Schedule on the finished task: only new or changed files", "incremental on; rerun the wizard", "run the same command again on cutover night", "no true delta"]),
]
yy = 214
for label, cells in rows:
    d.text(LX, yy + 18, label, 12.5, 600, C.ink)
    d.line(LX, yy + 60, 1232, yy + 60, C.rule, 1)
    for (letter, name, where, col, verdict), x, cell in zip(cols, xs, cells):
        d.lines(x + 6, yy + 16, cell, 11, CW - 12, 400, C.grey if col != C.red else C.red)
    yy += 66
# verdict row
d.text(LX, yy + 20, "Verdict", 12.5, 600, C.ink)
for (letter, name, where, col, verdict), x in zip(cols, xs):
    d.pill(x + 6, yy + 6, verdict, col, solid=(letter != "D"))

# ---------------- decision strip
d.zone(32, 666, 1216, 82, "Pick in this order", icon="question-diamond-gold")
d.card(48, 700, 268, 40, "", [], shadow=False, accent=C.blue)
d.text(60, 725, "More than a handful of folders → A", 12, 600, C.blue)
d.card(332, 700, 268, 40, "", [], shadow=False, accent=C.teal)
d.text(344, 725, "Scripted waves with evidence → C", 12, 600, C.teal)
d.card(616, 700, 268, 40, "", [], shadow=False, accent=C.purple)
d.text(628, 725, "A single share, no agent wanted → B", 12, 600, C.purple)
d.card(900, 700, 332, 40, "", [], shadow=False, accent=C.red)
d.text(912, 725, "Every tool blocked and only a few GB → D", 12, 600, C.red)

d.note_bottom("Limits that apply to every method: 400 decoded path characters, 250 GB per file, reserved names rejected (see the scan findings figure). Controls: CM-3, AC-3, SC-7.")
d.render(repo_path("microsoft-365/diagrams/sop-m365-001-3.svg"))
