import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("What actually reaches a VM: paper rules versus the effective view",
            "Azure evaluates inbound traffic subnet NSG then NIC NSG, lowest priority number first, first match wins; outbound runs the other way and then follows the effective route table.",
            height=800)

# ---------------- INBOUND lane
d.zone(32, 100, 1216, 300, "Inbound to the app VM", icon="download", note="evaluated subnet NSG → NIC NSG; first matching rule wins")
# source
d.card(48, 146, 150, 100, "Source", ["Internet, hub mgmt subnet, gateway subnet"], icon="globe", accent=C.grey)
d.arrow([(198, 192), (236, 192)], C.grey)
# subnet NSG stack
d.zone(238, 136, 520, 252, "Subnet NSG on snet-app (rules in priority order)", icon="firewall", fill="#fff")
rules = [
    ("100", "Allow SSH 22", "from hub mgmt subnet only", C.green, "Allow"),
    ("110", "Allow app port", "from gateway subnet only", C.green, "Allow"),
    ("4000", "Deny Internet inbound", "explicit, above defaults", C.red, "Deny"),
    ("65000", "AllowVnetInBound (default)", "any VNet incl. peered hub", C.grey, "Allow"),
    ("65500", "DenyAllInBound (default)", "the floor, hit last", C.grey, "Deny"),
]
yy = 176
for pri, title, body, col, verdict in rules:
    d.card(252, yy, 492, 38, "", [], accent=col, shadow=False, pill=(verdict, col))
    d.text(258, yy + 24, pri, 11, 600, col, "start")
    d.text(336, yy + 24, title, 12.5, 600, C.ink)
    d.text(534, yy + 24, body, 10.5, 400, C.grey, max_w=146)
    yy += 42
d.arrow([(758, 192), (796, 192)], C.grey)
d.card(798, 146, 190, 100, "NIC NSG", ["none on this NIC, so the subnet rules are the whole story"], icon="link", accent=C.grey, pill=("none", C.grey))
d.arrow([(988, 192), (1026, 192)], C.green)
d.card(1028, 146, 204, 100, "App VM", ["no public IP, so nothing arrives from the Internet to begin with"], icon="vm-cluster", accent=C.purple, pill=("no PIP", C.green))
d.callout(798, 258, 434, 126, "Effective security rules = subnet + NIC, merged", kind="info", icon="doc-check-green",
          body=["Read on the NIC under Help › Effective security rules. Azure computes it only while the VM runs, so the review is scheduled with the VMs up. That merged list, not the design diagram, is the evidence."])

# ---------------- OUTBOUND lane
d.zone(32, 416, 1216, 300, "Outbound from the app VM", icon="arrows-lr", note="NIC NSG → subnet NSG, then the effective route decides the exit")
d.card(48, 462, 150, 92, "App VM", ["service calls out on 443"], icon="vm-cluster", accent=C.purple)
d.arrow([(198, 508), (236, 508)], C.grey)
d.zone(238, 452, 330, 252, "Subnet NSG, outbound", icon="firewall", fill="#fff")
out_rules = [("200", "Allow 443 to AzureCloud", C.green, "Allow"), ("4000", "Deny all outbound", C.red, "Deny"),
             ("65000", "AllowVnetOutBound (default)", C.grey, "Allow"), ("65001", "AllowInternetOut (default)", C.grey, "Allow")]
yy = 492
for pri, title, col, verdict in out_rules:
    d.card(252, yy, 302, 38, "", [], accent=col, shadow=False, pill=(verdict, col))
    d.text(258, yy + 24, pri, 11, 600, col)
    d.text(306, yy + 24, title, 12.5, 600, C.ink)
    yy += 42
d.lines(252, 672, "The explicit deny at 4000 masks the default AllowInternetOutBound at 65001.", 11, 300)
d.arrow([(568, 508), (606, 508)], C.grey)
d.zone(608, 452, 330, 252, "Effective routes on the NIC", icon="hierarchy", fill="#fff")
routes = [("10.2.0.0/16", "Virtual network", "stays in the spoke", C.blue), ("10.0.0.0/16", "VNet peering", "to the hub only, never another stamp", C.blue),
          ("0.0.0.0/0", "Internet (via NAT gateway)", "fixed outbound IP; finding if a firewall was designed", C.gold)]
yy = 492
for prefix, hop, note, col in routes:
    d.card(622, yy, 302, 58, hop, [note], accent=col, shadow=False, title_size=12.5, body_size=11)
    d.text(916, yy + 20, prefix, 11, 600, col, "end", mono=True)
    yy += 64
d.arrow([(938, 508), (976, 508)], C.gold)
d.card(978, 462, 254, 100, "Exit point", ["NAT gateway (fixed IP) or, if the design says so, a firewall with an FQDN allow-list"], icon="cloud", accent=C.gold)
d.callout(978, 574, 254, 130, "Finding, not a pass", kind="warn",
          body=["Outbound 443 to any host is how stolen data leaves. No FQDN allow-list: record it with the accepted-risk decision and owner."])

# ---------------- bottom: evidence rule
d.note_bottom("Pass: no Allow rule with source Internet, Any or 0.0.0.0/0; public IPs only on gateways, NAT and Bastion; stamps peer only with the hub. Controls: SC-7, CM-6, CA-7.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-106-2.svg"))
