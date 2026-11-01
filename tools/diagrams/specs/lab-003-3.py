import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Standard versus qualified build: what qualification adds",
            "Same catalog, same profile, same depot. The qualified path adds Quality's decisions at the profile, the IQ at the build, and OQ, approval and change control after delivery.",
            height=760)

PITCH, W, H = 196, 186, 100

# ---------------- row 1: the shared path (Method A)
d.zone(32, 100, 1216, 156, "The shared path, Method A", icon="checklist-purple", note="step numbers follow the runbook")
steps = [
    ("3", "Funding code", "cost center from your manager; approver on the checklist"),
    ("4", "Configuration profile", "six sections in the build portal; the profile ID is the specification"),
    ("5", "Maintenance slot", "ConfigMgr window outside lab hours; a missed deadline waits for the next one"),
    ("6", "Time and DST", "audit trails are time-stamped: decide automatic DST deliberately"),
    ("7", "Catalog request", "New workstation order, profile ID linked, inventory attached"),
    ("8", "Build and deliver", "depot images to the profile, OU and collections, apps in order; you verify"),
]
for i, (n, t, b) in enumerate(steps):
    x = 48 + i * PITCH
    d.card(x, 144, W, H, t, [b], badge=n, accent=C.blue, shadow=False, title_size=12.5, body_size=11)
    if i < 5:
        d.arrow([(x + W, 194), (x + PITCH, 194)], C.blue, sw=1.6)

# ---------------- row 2: what Method B adds at those steps
d.zone(32, 272, 1216, 156, "What Method B adds at those steps", icon="certificate", fill=C.purpletint, stroke=C.purple, title_color=C.purple)
adds = {
    1: ("Qualification type set", "with Quality / CSV: automated IQ, a manual IQ protocol, or both; selected in the profile; prerequisites form attached"),
    2: ("GxP defaults kept", "screensaver lock, restricted access, minimal local admins, automatic-reboot window outside lab hours"),
    5: ("Depot records the IQ", "built exactly as the profile says: model, OS, applications and versions, settings"),
}
for i in range(6):
    x = 48 + i * PITCH
    if i in adds:
        t, b = adds[i]
        d.card(x, 316, W, H, t, [b], accent=C.purple, shadow=False, title_size=12.5, body_size=11)
        d.arrow([(x + W / 2, 244), (x + W / 2, 316)], C.purple, dashed=True, sw=1.4)
    else:
        d.rect(x, 316, W, H, fill="none", stroke=C.border, rx=5, dashed=True)
        d.text(x + W / 2, 370, "as Method A", 11.5, 400, C.light, "middle")

# ---------------- row 3: after delivery, qualified only
d.zone(32, 444, 1216, 150, "After delivery, qualified build only", icon="doc-check-purple", fill=C.purpletint, stroke=C.purple, title_color=C.purple,
       note="then every later change goes through the catalog")
after = [
    ("OQ, then PQ / UAT if required", "the lab or validation team runs it and resolves deviations: the application works on this PC and writes its audit trail"),
    ("Quality approves the summary", "the CMDB CI is marked Qualified; the evidence package is the baseline every later change is measured against"),
    ("Change control from now on", "one more tool, an extra admin, a different window collection: Request a change to my workstation; a rebuild repeats IQ and the OQ scope Quality sets"),
]
for i, (t, b) in enumerate(after):
    x = 48 + i * 400
    d.card(x, 488, 384, 94, t, [b], badge=str(i + 1), badge_color=C.purple, accent=C.purple, shadow=False, title_size=12.5, body_size=11)
    if i < 2:
        d.arrow([(x + 384, 535), (x + 400, 535)], C.purple, sw=1.6)
d.arrow([(1028 + W / 2, 416), (1028 + W / 2, 436), (240, 436), (240, 488)], C.purple, dashed=True, sw=1.4)

# ---------------- row 4: the three qualifications
d.card(32, 616, 392, 56, "IQ · Installation qualification", ["the PC was built exactly as the profile says"], icon="doc-check-green", accent=C.green, shadow=False, body_size=11.5)
d.card(444, 616, 392, 56, "OQ · Operational qualification", ["the application works on this PC and writes its audit trail"], icon="doc-check-green", accent=C.green, shadow=False, body_size=11.5)
d.card(856, 616, 392, 56, "PQ / UAT", ["the lab confirms fitness for intended use with real workflows"], icon="doc-check-green", accent=C.green, shadow=False, body_size=11.5)

d.note_bottom("Lead time about 1–3 weeks either way; an incomplete profile is the main cause of rework. A qualified rebuild is a separate service because it repeats the evidence. Controls: GAMP 5; GxP system lifecycle.")
d.render(repo_path("regulated-lab-it/diagrams/sop-lab-003-3.svg"))
