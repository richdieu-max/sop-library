import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("The isolated Hyper-V bridge: a time-boxed Windows 7 VM that reaches the instrument and nothing else",
            "The host stays patched and managed on the corporate NIC; the guest owns the instrument NIC through a vSwitch the host cannot use, and has no other network at all.",
            height=780)

# ---- corporate side (outside the host)
d.card(32, 146, 196, 84, "Corporate network", ["domain, patching, EDR, internet"], icon="globe", accent=C.blue)
d.arrow([(228, 188), (252, 188)], C.blue)
d.callout(32, 250, 196, 170, "Host is managed", kind="info", icon="shield-check",
          body=["Patched, enrolled and running EDR over the corporate NIC. Only the guest is unpatched, and it is boxed in."])

# ---- the host
d.zone(232, 100, 700, 428, "Windows 11 host", icon="monitor", note="Pro, Enterprise or Education · virtualization enabled in firmware")
d.card(252, 146, 200, 84, "Corporate NIC", ["DHCP address, used by the host only"], icon="link", accent=C.blue, pill=("host", C.blue))

d.zone(252, 262, 660, 186, "Hyper-V role on the host", icon="vm-cluster", note="Generation 1, because the guest is Windows 7", fill=C.paper)
d.card(268, 304, 304, 124, "Windows 7 VM · Gen 1",
       ["4 GB static memory: dynamic memory off so instrument timing stays predictable",
        "80 GB VHDX; automatic checkpoints off; AutomaticStartAction Start"],
       icon="w7-monitor", accent=C.gold, pill=("unpatched", C.red))
d.card(596, 304, 300, 124, "External vSwitch",
       ["bound to the Instrument NIC only; AllowManagementOS $false, so the host cannot use it",
        "legacy adapter until the integration components update is in the guest"],
       icon="arrows-lr-circle", accent=C.green, pill=("isolated", C.green))
d.arrow([(572, 366), (596, 366)], C.green)

# blocked path from the VM up to the corporate NIC
d.line(560, 304, 560, 188, C.red, 2, dashed=True)
d.line(560, 188, 452, 188, C.red, 2, dashed=True)
pw = d.pill(0, 0, "blocked: no corporate or internet path", C.red)  # measure
d.parts.pop(); d.parts.pop()
d.pill(560 - pw / 2, 232, "blocked: no corporate or internet path", C.red, solid=True)

d.card(596, 458, 300, 62, "Instrument NIC", ["static address, no gateway or DNS; handed to the vSwitch"], icon="ip-server", accent=C.green)
d.arrow([(746, 428), (746, 458)], C.green)

# ---- the instrument side (outside the host)
d.arrow([(746, 520), (746, 548)], C.green)
d.card(596, 548, 300, 60, "Isolated instrument switch", ["no uplink to anything else"], icon="ports-green", accent=C.green)
d.arrow([(896, 578), (940, 578)], C.gold)
d.card(940, 548, 308, 60, "Instrument controller", ["UDP control traffic; the only peer the VM can reach"], icon="instrument", accent=C.gold)

# ---- right column: containment and time-box
d.zone(956, 100, 292, 212, "Containment in the guest", icon="shield-x", fill=C.redtint, stroke=C.red, title_color=C.red)
d.card_col(970, 140, 264, 52, [
    {"title": "No corporate or internet network", "body": ["only adapter: the instrument vSwitch"], "accent": C.red},
    {"title": "Enhanced Session off", "body": ["clipboard and drive redirection off"], "accent": C.red},
    {"title": "No USB pass-through", "body": ["dongles need validated USB-over-IP"], "accent": C.red},
], gap=6, shadow=False, title_size=12.5, body_size=10.5)

d.zone(956, 326, 292, 212, "Time-box and evidence", icon="calendar", fill=C.goldtint, stroke=C.gold, title_color=C.gold)
d.card_col(970, 366, 264, 52, [
    {"title": "Exit date in the change record", "body": ["a bridge to the vendor upgrade"], "accent": C.gold},
    {"title": "Export-VM to controlled storage", "body": ["checkpoints are not backups"], "accent": C.gold},
    {"title": "Validated baseline checkpoint", "body": ["Restore-VMCheckpoint is the rollback"], "accent": C.gold},
], gap=6, shadow=False, title_size=12.5, body_size=10.5)

# ---- bottom: why these settings
d.callout(32, 624, 1216, 86, "Why Generation 1, static memory, automatic start and a legacy adapter", kind="note", icon="gear-box",
          body=["Windows 7 only boots as a Generation 1 VM; dynamic memory is off so control timing is predictable; AutomaticStartAction brings the guest back after a host reboot; the guest sees no network until the integration components update is installed, so it starts on a legacy adapter."])

d.note_bottom("Windows 7 has had no security fixes since January 2023, so the guest must never see the corporate network; confirm guest licensing. Controls: 21 CFR Part 11 §11.10(a); EU GMP Annex 11; GAMP 5.")
d.render(repo_path("regulated-lab-it/diagrams/sop-lab-001-3.svg"))
