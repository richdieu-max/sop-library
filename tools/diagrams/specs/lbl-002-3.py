import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("DORA with a reservation: where the MAC decides which address the printer gets",
            "The printer only asks when it boots, renews or is refused; the router relays the broadcast and stamps the scope; the server matches the MAC against reservations before it touches the pool.",
            height=780)

actors = [("Label printer (MAC on its configuration label)", "printer", C.gold),
          ("Router on the lab VLAN (ip helper-address)", "hierarchy", C.grey),
          ("DHCP server, scope 192.0.2.0", "server", C.blue)]
msgs = [
    (0, 1, "DISCOVER, broadcast, carries the printer MAC", C.gold, False),
    (1, 2, "relayed unicast; giaddr = router interface → selects the scope", C.grey, False),
    (2, 2, "reservation for this MAC in the scope?", C.blue, False),
    (2, 1, "OFFER 192.0.2.60 (reserved) with mask, gateway, DNS", C.blue, True),
    (1, 0, "OFFER forwarded to the printer", C.grey, True),
    (0, 1, "REQUEST: the printer accepts the offer", C.gold, False),
    (1, 2, "relayed", C.grey, False),
    (2, 2, "lease recorded; audit log event 10 (new) or 11 (renewal)", C.blue, False),
    (2, 0, "ACK: the lease is live", C.blue, True),
]
bottom = d.sequence(32, 100, 820, actors, msgs, lane_h=38, actor_h=52)

# ---- right column: the decision and the failure
d.zone(876, 100, 372, 206, "Reservation first, pool second", icon="question-diamond", fill=C.bluetint, stroke=C.blue)
d.card(892, 140, 340, 72, "MAC matches a reservation", ["the reserved address wins, every time; gateway, mask and DNS still come from the scope options"],
       accent=C.green, shadow=False, pill=("192.0.2.60", C.green), body_size=11.5)
d.card(892, 222, 340, 72, "No reservation for this MAC", ["next free pool address; the queue keeps pointing at .60 where nothing answers"],
       accent=C.red, shadow=False, pill=("pool lease", C.red), body_size=11.5)

d.callout(876, 322, 372, 214, "Why a replacement printer breaks", kind="warn",
          body=["The reservation for .60 still names the retired printer's MAC. The new unit has a new MAC, finds no match and takes a pool address, so every team's own check comes back \"looks fine\".",
                "Fix: rebind the reservation to the MAC on the configuration label, delete the stale leases for .60 and for the new MAC, replicate to the failover partner (reservations are not synchronised automatically), then power-cycle."])

# ---- bottom: audit log decoder
d.zone(32, bottom + 14, 820, 150, "What the DHCP audit log says", icon="doc-search", note="%windir%\\System32\\dhcp\\DhcpSrvLog-<Day>.log · search the MAC without separators")
rows = [["Event", "Meaning", "What it tells you"],
        ["10", "New lease", "the printer asked and got an address: check which one"],
        ["11", "Renewal", "the existing binding was renewed, nothing changed"],
        ["13", "Address in use", "conflict detection found another device on the address"],
        ["14", "Pool exhausted", "no free address left in the scope"],
        ["15", "Lease denied", "the server refused this client"]]
d.table(48, bottom + 52, [70, 150, 580], rows, row_h=18, size=10.5, col_colors=[C.blue, C.ink, None])

d.note_bottom("A device runs DORA only on boot, renewal or refusal, so a corrected reservation takes effect after a power-cycle. Controls: CM-3, CM-8, AC-6 (DHCP Administrators, not Domain Admins).")
d.render(repo_path("label-printing/diagrams/sop-lbl-002-3.svg"))
