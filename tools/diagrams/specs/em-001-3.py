import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Proving it worked: from enrolled Mac to a healthy sensor",
            "Six checks in order, each with the symptom that stops it and the fix; the Defender portal listing is the definitive pass.",
            height=824)

# ---------------- left: the ladder
d.zone(32, 100, 700, 560, "Verification ladder", icon="shield-check", note="climb in order; stop at the first rung that fails")
rungs = [
    ("Connector and group are ready", ["Intune › Endpoint security › Defender for Endpoint: connection Enabled with a recent sync; the dynamic Mac group has members"], "Intune", C.blue),
    ("App shows Installed", ["Intune app status for Microsoft Defender for Endpoint (macOS) reads Installed on every target device"], "Intune", C.blue),
    ("All eight profiles Succeeded", ["Intune device configuration: seven permission profiles plus the onboarding profile, each Succeeded on each Mac"], "Intune", C.blue),
    ("The Mac agrees", ["System Settings › Device Management lists the eight profiles; the Defender menu-bar icon reports Protected"], "on the Mac", C.purple),
    ("Listed in the Defender portal", ["Assets › Devices shows each Mac with a recent Last seen. This is the definitive check."], "definitive", C.green),
    ("Optional: EICAR detection test", ["Microsoft's EICAR test file is detected and reported, proving the sensor sees and acts"], "optional", C.grey),
]
y = 142
boxes = []
for i, (title, body, tag, col) in enumerate(rungs):
    d.card(48, y, 668, 70, title, body, badge=str(i + 1), accent=col, pill=(tag, col))
    boxes.append(y)
    if i < len(rungs) - 1:
        d.arrow([(82, y + 70), (82, y + 84)], col, sw=1.6)
    y += 84

# ---------------- right: what stops each rung
d.zone(760, 100, 488, 560, "If a rung fails", icon="wrench", note="symptom → fix")
fixes = [
    ("Connector Unresponsive · group has 0 members", ["Toggle the connection off, save, wait five minutes, toggle on. Remove the spaces inside the quotes of the group rule and allow 30 minutes."]),
    ("App never installs", ["The assignment must be Required; Available only offers it in Company Portal."]),
    ("A profile shows Error", ["An HTML page was saved instead of the raw file, or the profile used the User channel instead of the Device channel."]),
    ("User asked to approve the system extension", ["The sysext profile arrived after the app; confirm ownership is Corporate and the assignment reached the group."]),
    ("App installed, Mac missing from the portal", ["The onboarding profile is not assigned or has not applied; it is the eighth profile, device channel, same group."]),
    ("Nothing to fix", ["The test is optional; a detection simply confirms the earlier rungs."]),
]
y = 142
for i, (title, body) in enumerate(fixes):
    col = rungs[i][3]
    d.card(776, y, 456, 70, title, body, accent=col, shadow=False, title_size=12.5, body_size=11.5)
    d.arrow([(716, boxes[i] + 35), (776, boxes[i] + 35)], col, dashed=True, sw=1.4)
    y += 84

# ---------------- bottom: keep it healthy
d.callout(32, 676, 1216, 84, "Keep it healthy", kind="info", icon="calendar",
          body=["Re-check Microsoft's profile repository quarterly and refresh profiles that changed. The onboarding package is tenant-specific: a tenant rebuild means offboarding and re-onboarding every Mac."])

d.note_bottom("6 rungs, 5 fixes; 8 profiles Succeeded and 1 app Installed per Mac before the portal check. Controls: SI-3, SI-4 (protection and monitoring in place), CM-6 (configuration verified).")
d.render(repo_path("endpoint-management/diagrams/sop-em-001-3.svg"))
