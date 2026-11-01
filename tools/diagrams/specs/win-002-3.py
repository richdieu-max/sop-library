import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Before a lease exists: the start gate, the DORA exchange, and what ipconfig shows",
            "The SCM reads the dependency list only at start; once Dhcp runs, four messages decide the address, and each failure leaves a different ipconfig reading.",
            height=820)

# ---------------- top strip: the start gate
d.zone(32, 100, 1216, 128, "Start gate: what has to be true before Dhcp can start", icon="gear", note="SCM reads DependOnService at start only; a damaged PC works until its next restart")
gate = [("1", "SCM reads the list", "DependOnService = NSI / Tcpip / Afd", C.grey),
        ("2", "NSI running", "Network Store Interface, user mode", C.blue),
        ("3", "Tcpip loaded", "TCP/IP protocol kernel driver", C.blue),
        ("4", "Afd loaded", "Winsock kernel side", C.blue),
        ("5", "Dhcp starts", "svchost, as the LocalService account", C.green)]
for i, (n, t, b, col) in enumerate(gate):
    x = 48 + i * 240
    d.card(x, 140, 220, 70, t, [b], badge=n, badge_color=col, accent=col, shadow=False, title_size=12.5, body_size=11)
    if i < 4:
        d.arrow([(x + 220, 175), (x + 240, 175)], col, sw=1.6)
d.pill(48, 214, "1068 · a listed dependency failed: fix it, or restore the default list", C.red)
d.pill(470, 214, "1075 · the list names something missing: restore NSI/Tcpip/Afd", C.gold)
d.pill(900, 214, "1079 / 1069 · service account changed: restore LocalService", C.purple)

# ---------------- middle: DORA sequence
d.zone(32, 246, 820, 318, "DORA: the four-message exchange once Dhcp is running", icon="arrows-lr", note="UDP 67/68; broadcast until the client has an address")
actors = [("Workstation (Dhcp)", "monitor", C.green), ("Switch port, VLAN, relay", "link", C.grey), ("DHCP server", "server", C.blue)]
msgs = [
    (0, 2, "DISCOVER (broadcast): is there a server?", C.green, False),
    (2, 0, "OFFER: an address, mask, gateway, DNS", C.blue, True),
    (0, 2, "REQUEST: I will take that offer", C.green, False),
    (2, 0, "ACK: lease granted, with lease time", C.blue, True),
]
bottom = d.sequence(48, 288, 788, actors, msgs, lane_h=40, actor_h=48)
d.text(48, bottom + 16, "No reply to DISCOVER within the timeout: the client assigns itself 169.254.x.x (APIPA) and keeps retrying.", 11, 400, C.grey, max_w=790)

# ---------------- right: what ipconfig shows
d.zone(868, 246, 380, 318, "Read ipconfig /all first", icon="doc-search", note="connected adapter")
d.card(884, 288, 348, 78, "No IPv4 address at all", ["Dhcp is not running: the gate above failed. This runbook, Methods A to C."], accent=C.red, shadow=False, title_size=12.5, body_size=11, pill=("this SOP", C.red))
d.card(884, 376, 348, 78, "169.254.x.x", ["Dhcp runs, no server answered: cable, switch port, VLAN, 802.1X, scope exhausted or IP helper. Not a client fault."], accent=C.gold, shadow=False, title_size=12.5, body_size=11, pill=("network", C.gold))
d.card(884, 464, 348, 86, "A normal address", ["DHCP works. If the user still cannot log on, look further up the relay: DNS, DC locator, secure channel, Group Policy."], accent=C.green, shadow=False, title_size=12.5, body_size=11, pill=("look up the chain", C.green))

# ---------------- bottom: after the lease, in order
d.zone(32, 582, 1216, 150, "After the lease: re-establish the domain in this order (step 4)", icon="checklist-purple", note="each command must pass before the next one means anything")
after = [("ipconfig /renew", "then ipconfig /all: a real lease, gateway, corporate DNS", C.green),
         ("ipconfig /registerdns", "the PC's A record is back in DNS", C.green),
         ("nltest /dsgetdc", "must return a DC; if not, DNS or reachability", C.blue),
         ("nltest /sc_verify", "must end in NERR_Success; else repair the secure channel (step 6)", C.blue),
         ("gpupdate /force", "then gpresult /r /scope computer", C.purple),
         ("Restart", "Dhcp starts automatically, logon works, drives appear", C.purple)]
for i, (t, b, col) in enumerate(after):
    x = 48 + i * 200
    d.card(x, 624, 186, 92, t, [b], badge=str(i + 1), badge_color=col, accent=col, shadow=False, title_size=12, body_size=10.5)
    if i < 5:
        d.arrow([(x + 186, 670), (x + 200, 670)], col, sw=1.4)

d.note_bottom("Repair, in order of preference: fix a stopped dependency; restore sc config Dhcp depend= NSI/Tcpip/Afd; depend= / only as temporary recovery. Space after depend= is mandatory. Controls: CM-2, CM-6, IA-3.")
d.render(repo_path("windows-support/diagrams/sop-win-002-3.svg"))
