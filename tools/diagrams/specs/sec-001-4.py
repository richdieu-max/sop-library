import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Remediation channels: which route fixes which finding",
            "The fastest safe fix depends on what the finding is and where the device lives; every route ends in the same evidence: a post-fix scanner status and a change reference.",
            height=834)

# ---------------- the path from Defender into Intune (top strip)
d.zone(32, 100, 1216, 112, "How a Defender recommendation becomes an Intune task", icon="defender-shield", note="Advanced features › Microsoft Intune connection: On")
flow = [("Recommendation", ["Exploit available or active alert, sorted by exposed devices"], "doc-search", C.blue),
        ("Request remediation", ["type, SLA due date, priority, Open a ticket in Intune"], "ticket", C.blue),
        ("Intune security task", ["Endpoint security › Security tasks; Remediation › Activities"], "checklist-purple", C.purple),
        ("One action, one ticket", ["asset group, QIDs and CVEs closed, change ref, evidence"], "doc-check-green", C.green)]
x = 48
for i, (t, b, ic, col) in enumerate(flow):
    d.card(x, 138, 280, 62, t, b, icon=ic, accent=col, shadow=False, body_size=10.5)
    if i < 3:
        d.arrow([(x + 280, 169), (x + 296, 169)], C.grey)
    x += 296

# ---------------- matrix
d.zone(32, 228, 1216, 458, "Finding type × route", icon="heatmap")
routes = ["Intune update ring", "Intune expedited update", "Intune Win32 / EAM, uninstall assignment", "Maintenance window, scripted", "Linux package manager", "Configuration change", "Exception + compensating control"]
col_x0 = 372
col_w = 122
head_y = 280
for i, r in enumerate(routes):
    cx = col_x0 + i * col_w
    d.rect(cx, head_y - 20, col_w - 6, 46, fill=C.zone, stroke=C.border, rx=4)
    ls = r.split(" ", 1) if len(r) > 18 else [r]
    # wrap into up to 3 short lines
    from kit import wrap
    lines = wrap(r, 10.5, col_w - 16, 600)
    for li, line in enumerate(lines[:3]):
        d.text(cx + (col_w - 6) / 2, head_y - 4 + li * 13, line, 10.5, 600, C.ink, "middle")
P, A, N = "P", "A", None
findings = [
    ("Windows cumulative update", "quality update closes dozens of CVEs", [P, A, N, A, N, N, N]),
    ("P1 KEV on Windows endpoints", "exploited in the wild", [N, P, N, A, N, N, N]),
    ("Vulnerable third-party app", "upgrade or remove", [N, N, P, A, N, N, N]),
    ("End-of-support software", "Inventories › Software, EOS = Yes", [N, N, P, A, N, N, A]),
    ("Misconfiguration", "SMBv1 on, TLS below 1.2", [N, N, N, A, N, P, N]),
    ("Linux package", "dnf upgrade --security, apt-get --only-upgrade", [N, N, N, A, P, N, N]),
    ("Server outside Intune", "Tier 0/1: out of hours, snapshot, owner sign-off", [N, N, N, P, A, A, N]),
    ("Validated lab, medical, OT, vendor-managed", "scanned low-intensity, never patched blind", [N, N, N, N, N, A, P]),
]
ry = 314
for name, note, cells in findings:
    d.text(48, ry + 15, name, 12, 600, C.ink, max_w=316)
    d.text(48, ry + 30, note, 10.5, 400, C.grey, max_w=316)
    for i, v in enumerate(cells):
        cx = col_x0 + i * col_w
        if v == P:
            d.status_cell(cx, ry + 4, col_w - 6, 32, "primary", C.green)
        elif v == A:
            d.status_cell(cx, ry + 4, col_w - 6, 32, "alternative", C.blue)
        else:
            d.rect(cx, ry + 4, col_w - 6, 32, fill="#fff", stroke=C.rule, rx=3)
    ry += 42
d.line(48, ry + 2, 1232, ry + 2, C.rule, 1)
d.lines(48, ry + 18, "Every route ends the same way: wait for agent check-in or rescan, close only when Qualys shows Fixed and Defender no longer lists the device, then attach the scanner export, the KB or version check output, the change reference and the approver.", 10.5, 1176, 400, C.grey, lh=14)

# ---------------- verification strip
d.card(32, 700, 596, 66, "Before and after: the fleet KB check", ["Invoke-Command over the tier list reads Version.UBR, Get-HotFix and the pending-reboot key; the build number beats Get-HotFix because cumulative updates supersede"], icon="terminal-blue", accent=C.purple, shadow=False, body_size=11)
d.card(652, 700, 596, 66, "Rollback is a change of its own", ["pause the ring or assignment first; wusa /uninstall, redeploy the previous Win32 package, revert the single setting, dnf history undo; reopen the findings it had closed"], icon="refresh-green", accent=C.red, shadow=False, body_size=11)

d.note_bottom("Routes and fixes as named in Steps 3, 5 and 6 and the Rollback table. Controls: SI-2 (flaw remediation), SI-2(2) automated status, CM-8 asset inventory; CIS Controls v8 7.1–7.7.")
d.render(repo_path("security-operations/diagrams/sop-sec-001-4.svg"))
