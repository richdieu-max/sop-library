import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Address plan and routing: four ranges that must never overlap",
            "The client pool sits outside the virtual network, the gateway has its own /27, and the only rule into the VM subnet is RDP from that pool.",
            height=700)

# ---------------- outside: laptop + home network
d.zone(32, 100, 280, 356, "Outside Azure", icon="laptop", note="user's own network")
d.card(48, 140, 248, 86, "Admin laptop", ["Azure VPN Client; after connecting it holds one address from <client-pool>"], icon="laptop", accent=C.blue, body_size=11.5)
d.card(48, 240, 248, 86, "Home or office", ["Must not overlap any of the four Azure ranges, or the laptop cannot tell local from remote"], icon="wifi", accent=C.grey, body_size=11.5, pill=("no overlap", C.red))
d.card(48, 340, 248, 100, "<client-pool>  /24", ["Handed to connected laptops. Outside the VNet on purpose: Azure routes it through the gateway, not the subnet"], icon="ports-blue", accent=C.blue, body_size=11.5, pill=("outside", C.blue))

# ---------------- tunnel
d.arrow([(312, 183), (438, 183)], C.blue, label="OpenVPN · TLS 443", sw=2.2, label_dy=-10)
d.text(375, 204, "to the gateway public IP", 10.5, 400, C.grey, "middle")

# ---------------- VNet
d.zone(440, 100, 808, 356, "<vnet-range>  /16  · the virtual network", icon="cloud", fill=C.bluetint, stroke=C.blue, note="the gateway is the only internet-facing component")
d.zone(456, 140, 290, 300, "GatewaySubnet  /27", icon="hierarchy", fill="#fff", note="name is exact")
d.card(470, 180, 262, 96, "VPN gateway", ["Route-based, AZ SKU where available, new public IP; active-active and BGP off unless needed; 30 to 45 minutes to deploy"], icon="lock", accent=C.blue, body_size=11.5)
d.card(470, 290, 262, 72, "Nothing else lives here", ["Gateway only; no VMs, no other services"], icon="x-circle", accent=C.grey, body_size=11.5)
d.card(470, 372, 262, 60, "P2S configuration", ["pool <client-pool>, OpenVPN, Entra ID sign-in"], icon="gear-box", accent=C.purple, body_size=11.5)

d.arrow([(746, 228), (784, 228)], C.blue, sw=2.2)
d.zone(786, 140, 446, 300, "<vm-subnet>  /24", icon="server", fill="#fff", note="VMs, private IPs only")
d.card(802, 180, 414, 72, "NSG: allow 3389 from <client-pool> only", ["No inbound rule from the internet; the subnet never sees a public IP"], icon="firewall", accent=C.green, body_size=11.5, pill=("Allow", C.green))
d.card(802, 266, 198, 80, "VM, private IP", ["RDP target after the tunnel is up"], icon="vm-cluster", accent=C.purple, body_size=11.5)
d.card(1018, 266, 198, 80, "VM, private IP", ["same rule, same path"], icon="vm-cluster", accent=C.purple, body_size=11.5)
d.card(802, 360, 414, 68, "Route pushed to the client", ["Connected status shows a pool address and a route to <vnet-range>, so only VNet traffic enters the tunnel"], icon="arrows-lr", accent=C.blue, body_size=11.5)

# ---------------- rules strip
d.zone(32, 476, 1216, 140, "Overlap rules, in one line each", icon="checklist-purple")
rules = [
    {"title": "VNet and client pool", "body": ["Different ranges; the pool is not a subnet of the VNet"], "accent": C.blue, "icon": "arrows-lr-circle"},
    {"title": "VM subnet and GatewaySubnet", "body": ["Both inside the VNet, never overlapping each other"], "accent": C.blue, "icon": "hierarchy"},
    {"title": "Pool and the user's own network", "body": ["Overlap here breaks local routing on the laptop"], "accent": C.red, "icon": "wifi"},
    {"title": "Change the pool later?", "body": ["Any P2S change means re-downloading and redistributing the profile"], "accent": C.gold, "icon": "download"},
]
d.card_row(48, 516, 290, 86, rules, gap=12, body_size=11.5)

d.note_bottom("Sizes from the address plan: VNet /16, VM subnet /24, GatewaySubnet /27, client pool /24. Controls: SC-7 and CM-7 (no public IP on VMs), AC-17 (remote access only through the tunnel).")
d.render(repo_path("azure-procedures/diagrams/sop-az-004-2.svg"))
