import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Deployment profile matrix: four modes, two join types, one way a device finds its profile",
            "Pick the mode by who is present at first boot; Entra join is the standard and the group tag decides which profile and ESP the device receives.",
            height=790)

# ---------------- modes A–D
d.zone(32, 100, 1216, 208, "Four Autopilot modes", icon="laptop", note="letters are alternatives; A is the default")
modes = [
    ("A", "User-driven", "default", C.blue, ["who: the user, at home or in the office", "time: 30–90 minutes", "needs: network at the profile step", "profile: AP-UserDriven-STD"]),
    ("B", "Pre-provisioned", "technician + user", C.purple, ["who: IT or reseller runs the device phases (Win key ×5), user finishes", "time: user phase 10–20 minutes", "needs: TPM 2.0 attestation, physical device", "enabled by: allow pre-provisioned deployment = Yes"]),
    ("C", "Self-deploying", "no user", C.grey, ["who: nobody; kiosks and shared PCs", "needs: TPM 2.0 attestation", "target everything at the device", "group: Autopilot-KIOSK with Assigned Access or a shared multi-user profile"]),
    ("D", "Device preparation", "no hash", C.teal, ["who: the user", "no hardware hash; static device group", "Entra join and Windows 11 only", "a classic profile takes precedence"]),
]
for i, (letter, name, tag, col, body) in enumerate(modes):
    x = 48 + i * 300
    d.card(x, 140, 284, 152, name, body, badge=letter, badge_color=col, accent=col, pill=(tag, col), body_size=11)

# ---------------- join type and profile settings
d.zone(32, 324, 520, 212, "Join type", icon="entra-user")
d.card(48, 364, 488, 70, "Microsoft Entra joined: the standard", ["every mode above; cloud identity, Intune enrollment, Windows Hello for Business"], icon="check-circle", accent=C.green, shadow=False, pill=("standard", C.green))
d.card(48, 446, 488, 76, "Hybrid Entra joined: documented exception only", ["needs the Intune Connector for AD and domain controller line of sight during OOBE; the name template is not applied"], icon="warning", accent=C.gold, shadow=False, pill=("exception", C.gold))

d.zone(576, 324, 672, 212, "AP-UserDriven-STD: the settings that matter", icon="checklist-purple", note="assigned to Autopilot-STD")
prof = [
    ("Convert all targeted devices", "No, except a profile for an existing fleet", "No", C.red),
    ("Hidden pages", "licence terms, privacy, change account", "hidden", C.blue),
    ("Account type", "Standard user, never local admin", "Standard", C.green),
    ("Allow pre-provisioned", "a technician can run mode B", "Yes", C.green),
    ("Name template", "15 characters maximum", "CTS-%SERIAL%", C.purple),
    ("Deployment mode", "User-Driven, Microsoft Entra joined", "User-driven", C.blue),
]
for i, (name, why, val, col) in enumerate(prof):
    cx = 592 + (i % 2) * 328
    cy = 364 + (i // 2) * 54
    d.card(cx, cy, 312, 46, "", [], accent=col, shadow=False, pill=(val, col))
    d.text(cx + 14, cy + 18, name, 12, 600, C.ink)
    d.text(cx + 14, cy + 35, why, 10.5, 400, C.grey, max_w=206)

# ---------------- how a device finds its profile
d.zone(32, 552, 1216, 176, "How a device finds its profile", icon="hierarchy", note="profile is fetched at the network step of OOBE")
steps = [
    ("Hardware hash", ["OEM against the order, CSV import (≤500 rows, exact header) or Get-WindowsAutopilotInfo -Online"], "download", C.blue),
    ("Autopilot record", ["stamps the Entra device with [ZTDId]:<guid> and the group tag [OrderID]:STD"], "id-card", C.blue),
    ("Dynamic group", ["Autopilot-STD matches [OrderID]:STD; Autopilot-All matches any ZTDId"], "group-window", C.purple),
    ("Profile + ESP", ["AP-UserDriven-STD and ESP-STD are assigned to the group; status turns Assigned"], "policy-shield", C.green),
]
for i, (name, body, ic, col) in enumerate(steps):
    x = 48 + i * 300
    d.card(x, 592, 272, 78, name, body, icon=ic, accent=col, badge=str(i + 1), badge_color=col, body_size=11)
    if i < 3:
        d.arrow([(x + 272, 631), (x + 300, 631)], col)
d.chips(48, 684, [("STD", C.blue), ("EXEC", C.blue), ("LAB", C.blue), ("KIOSK", C.grey)])
d.text(290, 699, "group tags; correct a tag on the record rather than re-importing. A device registered after first boot needs a reset or a reboot back to OOBE before it sees the profile.", 11, 400, C.grey, max_w=930)

d.note_bottom("Sources: the mode table, step 4 (profile) and step 3 (dynamic groups) of this runbook. Controls: CM-2, CM-6 (one profile per persona), CM-8 and IA-3 (hash and serial identify the device).")
d.render(repo_path("endpoint-management/diagrams/sop-em-004-3.svg"))
