import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("SLA clocks and the exception lifecycle",
            "The clock starts when either scanner first sees the finding on that asset, not when a ticket is raised; a finding that cannot be fixed in time gets a dated, two-person exception.",
            height=756)

# ---------------- SLA clocks on a 0–90 day scale
d.zone(32, 100, 1216, 318, "Four priorities, four clocks", icon="clock", note="escalation when the clock runs out")
x0, x1 = 352, 1012
scale = (x1 - x0) / 90
for dd in (0, 7, 15, 30, 60, 90):
    px = x0 + scale * dd
    d.line(px, 150, px, 380, C.rule, 1)
    d.text(px, 146, f"day {dd}" if dd else "day 0", 10.5, 400, C.grey, "middle")
rows = [
    ("P1", "CISA KEV or verified exploit", 7, "72 h if internet-facing", C.red, "CISO the same day; emergency change"),
    ("P2", "Internet-facing or Tier 0, CVSS ≥ 7", 15, None, C.gold, "head of IT operations"),
    ("P3", "EPSS 0.10 or public exploit", 30, None, C.blue, "asset owner's manager"),
    ("P4", "CVSS 7 or more, no exploit signal", 90, None, C.grey, "monthly report"),
]
yy = 162
for pri, trigger, days, sub, col, esc in rows:
    d.card(48, yy, 290, 48, "", [], accent=col, shadow=False)
    d.badge(72, yy + 24, pri, col)
    d.text(92, yy + 20, trigger, 12, 600, C.ink, max_w=236)
    d.text(92, yy + 37, f"fix within {days} days", 11, 400, C.grey)
    d.parts.append(f'<rect x="{x0}" y="{yy + 14}" width="{scale * days:.0f}" height="20" rx="4" fill="{col}"/>')
    if sub:
        px = x0 + scale * 3
        d.line(px, yy + 10, px, yy + 38, C.ink, 1.5)
        d.text(px + 6, yy + 46, sub, 10.5, 400, C.ink)
    if days >= 60:
        d.text(x0 + scale * days - 8, yy + 28, f"{days} d", 11, 600, "#fff", "end")
    else:
        d.text(x0 + scale * days + 8, yy + 28, f"{days} d", 11, 600, col)
    d.text(1024, yy + 20, "if missed →", 10.5, 400, C.grey)
    d.lines(1024, yy + 36, esc, 11, 212, 600, col, lh=14)
    yy += 56
d.text(48, 394, "Each finding takes the highest priority any rule assigns. Low and informational findings wait for the next build refresh. One action, one ticket: a cumulative update closing dozens of CVEs is one change through the rings.", 10.5, 400, C.grey, max_w=1180)

# ---------------- exception lifecycle
d.zone(32, 434, 1216, 256, "When the fix cannot land in time: the exception lifecycle", icon="pause", fill=C.goldtint, stroke=C.gold, title_color=C.gold, note="no silent renewals")
steps = [
    ("Request", ["asset owner: reason and a planned fix date"], "user", C.gold),
    ("Assess", ["security: exposure and the compensating control"], "shield-check", C.gold),
    ("Approve", ["risk owner; two-person rule, never the requester"], "certificate", C.gold),
    ("Record", ["in Qualys, in Defender exception options, and in the register as a POA&M item"], "doc-check-green", C.gold),
    ("Expire", ["dated: example maximums P1 30 d, P2 90 d, P3 and P4 180 d"], "calendar", C.red),
    ("Re-review", ["fixed, or re-approved with a new date; an expired exception fails the weekly check"], "refresh-green", C.green),
]
x = 48
for i, (t, b, ic, col) in enumerate(steps):
    d.card(x, 476, 184, 96, t, b, icon=ic, accent=col, badge=str(i + 1), shadow=False, body_size=11)
    if i < 5:
        d.arrow([(x + 184, 524), (x + 198, 524)], C.gold)
    x += 198
d.card(48, 592, 384, 84, "Defender exception options", ["third party control · alternate mitigation · risk accepted · planned remediation"], icon="defender-shield", accent=C.blue, shadow=False, body_size=11)
d.card(448, 592, 384, 84, "Devices that stay on exceptions", ["validated lab instruments, medical, OT and vendor-managed devices: still scanned with low-intensity profiles, handled with compensating controls"], icon="instrument", accent=C.purple, shadow=False, body_size=11)
d.card(848, 592, 384, 84, "What the auditor checks", ["every exception has an expiry, an approver and a compensating control; none expired; sample closed tickets show post-fix scanner evidence"], icon="doc-search", accent=C.green, shadow=False, body_size=11)

d.note_bottom("Targets in the runbook: P1 100 % within SLA, P2 ≥ 95 %, P3 ≥ 90 %; MTTR P1 ≤ 7 d, P2 ≤ 15 d. Controls: SI-2, SI-2(2), CA-5 (POA&M), RA-5; CISA BOD 22-01 for KEV due dates.")
d.render(repo_path("security-operations/diagrams/sop-sec-001-3.svg"))
