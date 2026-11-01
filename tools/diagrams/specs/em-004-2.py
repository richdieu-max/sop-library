import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Enrollment Status Page: three phases, what each tracks, what blocks the user",
            "ESP-STD holds the desktop until the build is done; with use-on-error off, nobody ever gets a half-built laptop.",
            height=836)

# ---------------- the three phases
d.zone(32, 100, 1216, 262, "The three phases, in order", icon="hourglass", note="block until installed: Yes · error after 60 minutes")
phases = [
    ("Device preparation", "secure the device", ["join Microsoft Entra ID", "enroll in Intune", "TPM 2.0 attestation when no user is present (pre-provisioned, self-deploying)"], C.blue, "1"),
    ("Device setup", "device-targeted", ["policies, certificates, network profiles", "required apps targeted at the device", "the four blocking apps live here"], C.purple, "2"),
    ("Account setup", "user-targeted", ["user policies and user-targeted apps", "Windows Hello for Business set-up", "then the desktop appears"], C.green, "3"),
]
for i, (name, tag, body, col, n) in enumerate(phases):
    x = 48 + i * 400
    d.card(x, 140, 384, 118, name, body, badge=n, accent=col, pill=(tag, col), body_size=11.5)
    if i < 2:
        d.arrow([(x + 384, 199), (x + 400, 199)], col)
# who is present per mode
d.text(48, 284, "Who is present", 12, 600, C.ink)
d.text(48, 300, "per mode", 11, 400, C.grey)
modes = [("A", "User-driven", [("user", C.blue), ("user", C.blue), ("user · 30–90 min total", C.blue)]),
         ("B", "Pre-provisioned", [("technician · Win key ×5", C.purple), ("technician · green screen, reseal", C.purple), ("user · 10–20 min", C.green)]),
         ("C", "Self-deploying", [("device only", C.grey), ("device only · target everything at the device", C.grey), ("no account phase", C.grey)])]
yy = 272
for letter, name, cells in modes:
    d.badge(174, yy + 12, letter, C.ink, r=10, size=10.5)
    d.text(190, yy + 16, name, 11.5, 600, C.ink)
    for ci, (label, col) in enumerate(cells):
        d.status_cell(300 + ci * 312, yy, 300, 24, label, col)
    yy += 28
# (preparation / setup / account columns line up under the phase cards)

# ---------------- ESP settings
d.zone(32, 378, 560, 290, "ESP-STD, setting by setting", icon="checklist-purple", note="assigned to Autopilot-STD")
settings = [
    ("Show progress", "the user sees what is happening", "Yes", C.green),
    ("Error after", "the time-out that raises 0x800705b4", "60 min", C.gold),
    ("Custom message", "service desk number on the page", "set", C.blue),
    ("Log collection", "diagnostics kept when a build fails", "Yes", C.green),
    ("Only OOBE devices", "existing devices never see the ESP", "Yes", C.green),
    ("Block until installed", "desktop waits for the selected apps", "Yes", C.green),
    ("Allow reset on error", "user or technician can start over", "Yes", C.green),
    ("Allow use on error", "no half-built device reaches a user", "No", C.red),
]
for i, (name, why, val, col) in enumerate(settings):
    cx = 48 + (i % 2) * 276
    cy = 418 + (i // 2) * 60
    d.card(cx, cy, 262, 50, "", [], accent=col, shadow=False, pill=(val, col))
    d.text(cx + 14, cy + 19, name, 12, 600, C.ink)
    d.text(cx + 14, cy + 36, why, 10.5, 400, C.grey, max_w=180)

# ---------------- blocking apps
d.zone(616, 378, 632, 290, "Block only on selected apps: each one is a single point of failure", icon="warning", fill=C.goldtint, stroke=C.gold, title_color=C.gold)
apps = [("Company Portal", "app-window"), ("Defender configuration", "defender-shield"), ("VPN client", "lock"), ("One core LOB app", "package")]
for i, (name, ic) in enumerate(apps):
    cx = 632 + (i % 2) * 308
    cy = 418 + (i // 2) * 60
    d.card(cx, cy, 292, 52, name, ["must install, or the ESP fails"], icon=ic, accent=C.gold, shadow=False, title_size=12.5, body_size=11)
d.callout(632, 540, 300, 118, "When 0x800705b4 appears", kind="warn",
          body=["A blocking app failed or was slow, or Win32 and legacy MSI installs collided.",
                "Read the IME log (IntuneManagementExtension\\Logs) first."])
d.card(948, 540, 284, 52, "Fix or remove the app", ["raise the 60-minute time-out only after"], badge="1", accent=C.gold, shadow=False, body_size=11)
d.card(948, 600, 284, 56, "Collect, then reset", ["MdmDiagnosticsTool before any reset"], badge="2", accent=C.gold, shadow=False, body_size=11)

# ---------------- outcomes strip
d.zone(32, 684, 1216, 76, "How a build ends", icon="target")
d.card(48, 716, 380, 36, "", [], icon="check-circle", accent=C.green, shadow=False)
d.text(94, 739, "Green: desktop, or reseal and ship if pre-provisioned", 12, 600, C.ink, max_w=326)
d.card(444, 716, 380, 36, "", [], icon="x-circle", accent=C.red, shadow=False)
d.text(490, 739, "Red: view diagnostics, then reset; use on error is No", 12, 600, C.ink, max_w=326)
d.card(840, 716, 392, 36, "", [], icon="doc-check-green", accent=C.blue, shadow=False)
d.text(886, 739, "Evidence: Autopilot deployments report, ESP duration", 12, 600, C.ink, max_w=338)

d.note_bottom("ESP-STD: progress shown, 60-minute time-out, log collection on, OOBE devices only, reset allowed, use on error off, four blocking apps. Controls: CM-2, CM-6, SC-28 (BitLocker lands in the device phase).")
d.render(repo_path("endpoint-management/diagrams/sop-em-004-2.svg"))
