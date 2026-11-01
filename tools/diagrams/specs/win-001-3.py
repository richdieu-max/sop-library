import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Choosing a method A to E, and the Remediation loop that fixes a fleet",
            "Read the symptom and the problem code first; each one points at one method, and only Method E runs the same fix on every instrument PC without a visit.",
            height=790)

# ---------------- left: symptom -> method chooser
d.zone(32, 100, 744, 480, "Symptom to method", icon="question-diamond-gold", note="Device Manager code and Troubleshooting table")
sym = [
    ("Nothing changes when you plug in", "no new entry, no sound: cable, port or adapter", C.grey),
    ("Other devices, Code 28", "no driver for VID 0403 / 067B / 10C4 / 1A86", C.blue),
    ("Code 10 or 43 after an update", "regression, or a clone chip the driver refuses", C.blue),
    ("Code 52, or installs stall", "catalog, component store or WU damage", C.purple),
    ("COM number changed or \"in use\"", "ghost port (Code 45) still holds the number", C.teal),
    ("Works after reboot, fails after idle", "USB selective suspend", C.gold),
    ("Same fault on many instrument PCs", "fix once, apply to the fleet", C.green),
]
sy = [146 + i * 56 for i in range(len(sym))]
for (t, b, col), y in zip(sym, sy):
    d.card(48, y, 300, 48, t, [b], accent=col, shadow=False, title_size=12.5, body_size=11)

meth = [
    ("A", "Device Manager", "triage, driver fix, ghost removal, reassign the COM number", C.blue),
    ("B", "Command Prompt repair", "DISM then SFC, WU component reset, pnputil re-detect", C.purple),
    ("C", "PowerShell and pnputil", "inventory, remove ghosts, stage the signed driver", C.teal),
    ("D", "Power management", "selective suspend off: device, power plan, or machine-wide", C.gold),
    ("E", "At scale", "Invoke-Command for a few PCs, Intune Remediation for a fleet", C.green),
    ("—", "Not a Windows fix", "hardware swap, application line settings, wiring", C.grey),
]
my = [146 + i * 68 for i in range(len(meth))]
for (letter, t, b, col), y in zip(meth, my):
    d.card(452, y, 308, 62, t, [b], badge=letter, badge_color=col, accent=col, shadow=False, title_size=12.5, body_size=11)

# arrows: symptom index -> method index, routed through a per-target vertical lane
routes = [(0, 5), (1, 0), (2, 0), (3, 1), (4, 2), (5, 3), (6, 4)]
lane = {0: 372, 1: 384, 2: 396, 3: 408, 4: 420, 5: 432}
for si, mi in routes:
    y1 = sy[si] + 24
    y2 = my[mi] + 31
    col = meth[mi][3]
    d.arrow([(348, y1), (lane[mi], y1), (lane[mi], y2), (452, y2)], col, sw=1.6)
d.lines(48, 548, "Clone chips (PL2303HXA, CH340 copies) refused with Code 10: Method A ends with a genuine adapter, not a driver.", 10.5, 300, 400, C.grey, lh=14)

# ---------------- right: Method E remediation loop
d.zone(800, 100, 448, 480, "Method E · Remediation loop", icon="sync-purple", note="SYSTEM, 64-bit, instrument PCs")
d.card(816, 140, 416, 60, "Assign the pair", ["Intune › Devices › Scripts and remediations › Remediations, scoped to the instrument workstation group"], badge="1", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.card(816, 212, 198, 90, "Detection script", ["exit 1 when a Ports device has a problem code or selective suspend is enabled"], badge="2", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.card(1034, 212, 198, 90, "Remediation script", ["disable selective suspend, restart the problem ports"], badge="3", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.arrow([(1014, 257), (1034, 257)], C.red, label="exit 1", label_dy=-8)
d.card(816, 316, 198, 60, "Exit 0", ["compliant: nothing runs, the report shows it"], accent=C.green, shadow=False, title_size=12.5, body_size=11, pill=("pass", C.green))
d.arrow([(915, 302), (915, 316)], C.green, sw=1.6)
d.card(1034, 316, 198, 60, "Re-detect", ["next schedule proves the fix held"], accent=C.gold, shadow=False, title_size=12.5, body_size=11)
d.arrow([(1133, 302), (1133, 316)], C.gold, sw=1.6)
d.arrow([(1232, 346), (1242, 346), (1242, 206), (915, 206), (915, 212)], C.gold, sw=1.4, dashed=True)
d.card(816, 396, 416, 60, "Report", ["Intune shows the detection and remediation status per device; attach it as evidence"], badge="4", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.text(816, 484, "Deploy alongside the loop", 12.5, 600, C.ink)
d.pill(816, 494, "drivers as a Win32 app: pnputil /add-driver .\\*.inf /install", C.blue)
d.pill(816, 520, "pin versions with Windows driver update policies", C.blue)
d.pill(816, 546, "allow the Ports class for non-admins by Group Policy", C.blue)

# ---------------- bottom strip: the script behind A to E
d.zone(32, 596, 1216, 112, "One script behind Methods B to E: Repair-UsbSerial.ps1", icon="terminal-blue", note="-ExpectedPort COM3 -RepairOs -ResetWindowsUpdate -RemoveGhostPorts -WhatIf")
sw = [("Inventory", "Ports class, GetPortNames, SERIALCOMM key", C.blue), ("-RepairOs", "DISM CheckHealth, RestoreHealth, then SFC", C.purple),
      ("-ResetWindowsUpdate", "stop four services, rename the two folders", C.purple), ("-RemoveGhostPorts", "pnputil /remove-device per hidden port", C.teal),
      ("Selective suspend", "powercfg value 0 for AC and DC", C.gold), ("JSON evidence", "before and after, for the ticket", C.green)]
for i, (t, b, col) in enumerate(sw):
    d.card(48 + i * 200, 636, 186, 58, t, [b], accent=col, shadow=False, title_size=12, body_size=10.5)

d.note_bottom("Time: 15 minutes for a driver or port fix, 45 for an OS repair. Every change needs the device's LAPS password, not a shared account. Controls: CM-3, CM-7, CM-11, AC-6, SI-7.")
d.render(repo_path("windows-support/diagrams/sop-win-001-3.svg"))
