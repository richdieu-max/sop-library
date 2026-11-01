import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("What an electronic signature carries, and the evidence package an auditor opens",
            "A Part 11 signature is four properties bound to one record; the evidence behind it is a set of files that each identify the system, the time and the person without any explanation.",
            height=770)

# ---------------- left: signature anatomy
d.zone(32, 100, 500, 330, "Anatomy of one approval signature", icon="certificate", note="§11.50 · 11.70 · 11.100 · 11.200")
# the signature "stamp"
sx, sy = 48, 140
d.rect(sx, sy, 468, 92, fill="#fff", stroke=C.purple, sw=1.4, rx=5)
d.rect(sx, sy, 4, 92, fill=C.purple, stroke=C.purple, rx=0)
d.text(sx + 18, sy + 24, "Approved by  A. Reviewer (QA/CSV)", 13.5, 600, C.ink)
d.text(sx + 18, sy + 44, "2026-10-12 09:41:07 UTC", 12, 400, C.grey, mono=True)
d.text(sx + 18, sy + 64, "Meaning: Approved for implementation", 12, 400, C.ink)
d.text(sx + 18, sy + 82, "Record: CHG0012345 · signed in the validated quality system", 11, 400, C.grey)
d.pill(sx + 360, sy + 10, "Part 11 signature", C.purple)
# the four properties
props = [
    ("Name, date-time, meaning", "§11.50: the three things every signature shows", C.purple),
    ("Linked to its record", "§11.70: cannot be excised, copied or moved to another record", C.purple),
    ("Unique to one person", "§11.100: never reused, never shared", C.purple),
    ("Two components, re-auth", "§11.200: ID plus password or token at the moment of signing", C.purple),
]
grid = [(48, 244), (286, 244), (48, 338), (286, 338)]
for i, ((t, b, col), (gx, gy)) in enumerate(zip(props, grid)):
    d.card(gx, gy, 230, 86, t, [b], badge=str(i + 1), accent=col, shadow=False, body_size=10.5, title_size=12.5)
d.callout(32, 446, 500, 82, "Not an approval", kind="warn", body=["An email saying \"approved\" pasted into a work note: no meaning, no link, no second component, no re-authentication."])

# ---------------- right: the evidence package, in opening order
d.zone(556, 100, 692, 418, "The package, in the order an auditor opens it", icon="folder", note="attached to the record, never sent by email")
items = [
    ("Signed approval", "timestamp precedes the actual start time, or the emergency authorization is recorded", "certificate", C.purple),
    ("Baseline capture", "the evidence header: hostname, user, date-time with offset, OS build, time source (w32tm)", "terminal-blue", C.blue),
    ("Step log", "each actual result beside its expected result; testers sign and date each step as executed", "checklist-purple", C.blue),
    ("Named screenshots", "hostname, date, time, user and version visible; named by the convention below", "monitor", C.blue),
    ("IQ · OQ · PQ evidence", "installed state; application, roles and audit trail work; a run matches the reference system", "doc-check-green", C.green),
    ("Deviations and PIR", "failed, skipped or unplanned steps recorded as such; a missing screenshot is a gap, never recreated", "warning", C.red),
    ("Closure", "CMDB and configuration specification updated; QA signs: Evidence reviewed; system in validated state", "doc-check-purple", C.purple),
]
y = 140
for i, (t, b, ic, col) in enumerate(items):
    d.card(572, y, 660, 46, t, [b], icon=ic, accent=col, badge=str(i + 1), badge_color=col, shadow=False, body_size=10.5, title_size=12.5)
    y += 52

# ---------------- bottom: filename anatomy
d.zone(32, 540, 1216, 162, "Anatomy of a screenshot name", icon="hash-doc", note="<CHANGE>_<STAGE-STEP>_<HOSTNAME>_<YYYYMMDD-HHMM>.<ext>")
fx = 48
d.text(fx, 590, "CHG0012345_OQ-03_LAB-WS-014_20261012-1042.png", 20, 600, C.ink, mono=True)
parts = [("CHG0012345", "the change record", C.purple, 0), ("OQ-03", "stage and step it proves", C.blue, 1), ("LAB-WS-014", "the system, so it can never be mistaken", C.teal, 2), ("20261012-1042", "capture time, checked against the window", C.gold, 3)]
cw = 12.1
offsets = [0, 11, 17, 28]
card_x = [48, 350, 652, 954]
levels = [620, 613, 606, 599]
for (label, body, col, _), off, cx, lv in zip(parts, offsets, card_x, levels):
    px = fx + off * cw
    seg_w = len(label) * cw
    d.parts.append(f'<rect x="{px:.0f}" y="594" width="{seg_w:.0f}" height="3" fill="{col}"/>')
    mid = cx + 145
    sx_ = px + seg_w / 2
    d.parts.append(f'<polyline points="{sx_:.0f},597 {sx_:.0f},{lv} {mid},{lv} {mid},628" fill="none" stroke="{col}" stroke-width="1.8"/>')
    d.card(cx, 630, 290, 54, label, [body], accent=col, shadow=False, body_size=11, title_size=12.5)
d.text(700, 590, "Keep the header script window in frame beside the application while capturing.", 10.5, 400, C.grey, max_w=540)
d.note_bottom("Evidence stages for a workstation OS upgrade: IQ (versions, hostname, domain, time source, agents), OQ (instrument link, roles, audit trail, data path), PQ (run matches the reference). Controls: §11.10(a), (e), (k); CM-3, CM-4.")
d.render(repo_path("governance/diagrams/sop-gov-001-3.svg"))
