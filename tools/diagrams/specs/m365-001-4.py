import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("What the scan finds, and how each finding is fixed before the copy starts",
            "Migration Manager scans before it moves anything; the cleanup template turns the scan log into renames, removals, quarantine moves and a ManualReview list; then scan again.",
            height=772)

# ---------------- loop across the top
d.zone(32, 100, 1216, 196, "The remediate loop: scan, clean, review, re-scan until READY TO MIGRATE", icon="refresh-green", note="repeat until the scan shows no warnings")
steps = [
    ("Scan the source", ["Scans › Add source path (or a CSV of paths); Automatically scan content; wait for the result"], C.blue),
    ("Get the scan log", ["save to the evidence folder; filter ResultCode to the non-blank rows"], C.blue),
    ("Cleanup, -WhatIf", ["Invoke-PreMigrationCleanup.ps1 reads the log: removes junk, renames fixable names, flags the rest ManualReview"], C.purple),
    ("Review with owner", ["every ManualReview line is a decision; long paths get shorter names agreed now"], C.gold),
    ("Run, quarantine on", ["-QuarantineRoot moves items instead of deleting; a CSV records every action"], C.purple),
    ("Re-scan", ["MIGRATION WARNINGS FOUND means back to step 2; READY TO MIGRATE means copy to a task"], C.green),
]
x = 48
for i, (t, b, col) in enumerate(steps):
    d.card(x, 142, 186, 138, t, b, badge=str(i + 1), badge_color=col, accent=col, shadow=False, title_size=12.5, body_size=10.5)
    if i < 5:
        d.arrow([(x + 186, 211), (x + 200, 211)], col)
    x += 200
d.arrow([(1148, 280), (1148, 288), (140, 288), (140, 282)], C.green, dashed=True, label="warnings found: loop", label_dy=16)

# ---------------- findings table
d.zone(32, 312, 1216, 322, "Finding by finding", icon="doc-search", note="codes as they appear in the scan log ResultCode column")
rows = [["Finding", "Why SharePoint rejects it", "Fix", "Who"],
        ["INVALID_SHAREPOINT_NAME", ".lock, CON, PRN, AUX, NUL, COM0–COM9, LPT0–LPT9, desktop.ini, names with _vti_, names starting ~$, leading or trailing spaces", "cleanup script renames fixable names, removes junk; trailing spaces or dots handled through the \\\\?\\UNC\\ prefix", "script"],
        ["ITEM_IS_EMPTY", "zero-byte files are debris", "removed by the cleanup, or accepted as skipped", "script"],
        ["Hidden files (Thumbs.db)", "not content; migrated as noise if left", "removed; hidden items off in the task settings", "script"],
        ["Path too long", "more than 400 decoded characters once the site URL is prepended; the site path alone already uses 87", "migrate the subtree to a shallower folder, or agree shorter names with the owner", "owner"],
        ["Very large files", "files over 250 GB are refused", "installers, ISO and PST go to archive, not to Teams", "owner"],
        ["Access denied on a subfolder", "agent account lacks share or NTFS Read where inheritance is broken", "grant Read to the service account, then rescan", "admin"],
        ["Copied ACLs", "Preserve file share permissions would create thousands of unique item permissions", "leave it off; re-express access as team, channel or private-channel membership", "owner"]]
colw = [196, 420, 460, 108]
colx = [48]
for w in colw[:-1]:
    colx.append(colx[-1] + w)
yy = 352
from kit import wrap
for ri, row in enumerate(rows):
    is_h = ri == 0
    nl = 1 if is_h else max(len(wrap(c, 10.5, colw[ci] - 14)) for ci, c in enumerate(row))
    rh = 26 if is_h else 14 + 14 * nl
    d.parts.append(f'<rect x="48" y="{yy}" width="{sum(colw)}" height="{rh}" fill="{C.zone if is_h else ("#fff" if ri % 2 else "#FCFCFB")}" stroke="{C.border if is_h else C.rule}" stroke-width="1"/>')
    for ci, c in enumerate(row):
        if is_h:
            d.text(colx[ci] + 7, yy + 17, c, 11, 600, C.ink)
        else:
            col = C.ink if ci == 0 else (C.blue if ci == 3 else C.grey)
            d.lines(colx[ci] + 7, yy + 18, c, 10.5, colw[ci] - 14, 600 if ci == 0 else 400, col, lh=14)
    yy += rh
table_end = yy

# ---------------- bottom: what the cleanup writes
d.card(48, 650, 390, 62, "Evidence the cleanup leaves", ["a CSV of every rename, removal and quarantine move, attached to the change"], icon="doc-check-green", accent=C.green, shadow=False, body_size=11)
d.card(454, 650, 390, 62, "Quarantine, not delete", ["\\\\fileserver01\\quarantine\\<change> keeps the path structure, so anything needed moves back"], icon="folder-share", accent=C.gold, shadow=False, body_size=11)
d.card(860, 650, 372, 62, "Find long paths early", ["measure each item's future URL before the copy; do not discover it in the failure report"], icon="ruler", accent=C.blue, shadow=False, body_size=11)

d.note_bottom("Limits: 400 decoded path characters, 250 GB per file. Fix, then rerun the task: only failed or changed items copy. Controls: CM-3 (-WhatIf and CSV evidence), AC-3 (membership, not ACLs), CP-9 (quarantine).")
d.render(repo_path("microsoft-365/diagrams/sop-m365-001-4.svg"))
