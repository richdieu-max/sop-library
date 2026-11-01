import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Choosing A, B or C, and the integration path every method shares",
            "Three ways to fix the address, chosen by whether DHCP serves the lab VLAN and how repeatable the change must be; all of them end in the same queue, BarTender and LIMS steps.",
            height=790)

# ---------------- chooser
d.zone(32, 100, 1216, 250, "Fix the address", icon="ip-server", note="a pool lease is never acceptable: the queue port holds one IP forever")
d.card(48, 142, 250, 190, "DHCP on the lab VLAN?", ["Yes: reserve the address centrally so gateway, mask and DNS keep coming from the scope and the change is auditable.", "No, or Networking requires a static address: Method C."],
       icon="question-diamond-gold", accent=C.gold, body_size=11.5)
d.arrow([(298, 200), (330, 200)], C.green, label="yes")
d.arrow([(298, 300), (316, 300), (316, 342), (850, 342), (850, 300), (868, 300)], C.red, label="no DHCP", label_dy=-7)
d.card(332, 142, 240, 150, "DHCP console (GUI)", ["One device at a time. dhcpmgmt.msc: find the stale binding, back up, rebind or create (type Both), delete stale leases, replicate, power-cycle"],
       badge="A", badge_color=C.blue, accent=C.blue, body_size=11.5)
d.card(588, 142, 264, 150, "PowerShell template", ["Repeatable, with evidence. Set-PrinterReservation.ps1 inspects IP and MAC, exports the scope, removes stale bindings, adds the reservation, replicates to the failover partner, writes JSON. -WhatIf first"],
       badge="B", badge_color=C.purple, accent=C.purple, body_size=11.5)
d.card(868, 142, 364, 150, "Static address on the printer", ["Front panel, web page or SGD over port 9100: IP protocol Permanent, address, mask, gateway. Record it in IPAM and exclude it from every pool, or a conflict follows. It breaks if the printer changes subnet"],
       badge="C", badge_color=C.grey, accent=C.grey, pill=("no DHCP only", C.red), body_size=11.5)
d.text(332, 318, "A and B both leave a central, auditable record; B adds JSON evidence and failover replication.", 11, 400, C.grey, max_w=500)

# ---------------- shared path
d.arrow([(640, 350), (640, 378)], C.ink)
d.zone(32, 380, 1216, 224, "Method D · every method finishes here (print / BarTender server)", icon="printer", note="the queue name is what BarTender and the LIMS know; it never changes")
steps = [
    ("Test the raw port", "Test-NetConnection 192.0.2.60 -Port 9100 must succeed from the server", C.blue),
    ("Add the port", "Add-PrinterPort IP_192.0.2.60, Standard TCP/IP, raw 9100", C.blue),
    ("Check the driver", "ZPL driver that matches the printhead resolution (SOP-LBL-001)", C.blue),
    ("Create the queue", "Add-Printer, for example LAB-PRN-01 (Large), on that port and driver", C.blue),
    ("BarTender", "test format: File › Print › Document Properties shows driver and stock; Integration Builder lists the queue", C.teal),
    ("LIMS", "the LIMS administrator registers the exact queue name; one label from each with the lab present", C.teal),
]
x = 48
for i, (t, b, col) in enumerate(steps):
    d.card(x, 422, 186, 118, t, [b], badge=str(i + 1), badge_color=col, accent=col, shadow=False, body_size=11)
    if i < 5:
        d.arrow([(x + 186, 481), (x + 200, 481)], col)
    x += 200
d.callout(48, 548, 1184, 48, "Address change only: keep the queue", kind="ok", icon="check-circle")
d.text(380, 578, "Add-PrinterPort for the new address, then Set-Printer -Name '<queue>' -PortName 'IP_<new address>'. Every BarTender and LIMS reference stays the same.", 11.5, 400, C.grey)

# ---------------- verify ladder
d.zone(32, 620, 1216, 110, "Verify layer by layer; the first failing check names the owning team", icon="checklist-purple")
checks = [("Configuration label", "IP, mask, gateway, expected MAC", C.gold), ("DHCP (A/B)", "reservation shows the MAC, lease active", C.blue),
          ("ARP, same VLAN", "Get-NetNeighbor maps IP to the printer MAC", C.blue), ("TCP 9100", "Test-NetConnection from the print server", C.purple),
          ("DNS (if requested)", "Resolve-DnsName LAB-PRN-01.contoso.com", C.purple), ("Labels", "BarTender and LIMS labels accepted by the lab", C.teal)]
x = 48
for i, (t, b, col) in enumerate(checks):
    d.card(x, 656, 190, 60, t, [b], accent=col, shadow=False, title_size=12.5, body_size=10.5)
    if i < 5:
        d.arrow([(x + 190, 686), (x + 200, 686)], C.grey, sw=1.5)
    x += 200

d.note_bottom("Order of work: fix the address (A, B or C), then port, queue, driver, BarTender, LIMS, then verify bottom-up. Controls: CM-3, CM-8, SC-7 (TCP 9100 only through the firewall).")
d.render(repo_path("label-printing/diagrams/sop-lbl-002-4.svg"))
