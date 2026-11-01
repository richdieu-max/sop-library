import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("From sign-in to tunnel: what happens when a user clicks Connect",
            "The laptop never talks to a VM until Entra ID has issued a token for the Azure VPN application and the gateway has accepted it; the private IP only answers from inside the tunnel.",
            height=740)

actors = [("Admin laptop (Azure VPN Client)", "laptop", C.blue), ("Microsoft Entra ID", "entra-user", C.purple),
          ("VPN gateway (public IP)", "lock", C.gold), ("VM, private IP only", "vm-cluster", C.green)]
msgs = [
    (0, 0, "Import azurevpnconfig.xml once per device", C.blue, False),
    (0, 1, "sign in: organisational account, Azure VPN app", C.blue, False),
    (1, 1, "Conditional Access evaluates; MFA approved", C.purple, False),
    (1, 0, "token for the Azure VPN Client (issuer <tenant-id>)", C.purple, True),
    (0, 2, "OpenVPN over TLS 443 with the token", C.blue, False),
    (2, 2, "tenant, issuer and audience match the P2S configuration", C.gold, False),
    (2, 0, "connected: a <client-pool> address and a route to <vnet-range>", C.gold, True),
    (0, 3, "RDP 3389 to the private IP, allowed from the client pool only", C.green, False),
    (3, 0, "session; disconnect when finished", C.green, True),
]
bottom = d.sequence(32, 100, 870, actors, msgs, lane_h=38)

# right column: what the one-time build put in place for this to work
d.zone(922, 100, 326, bottom - 100, "The one-time build behind it", icon="checklist-purple", note="steps 4 to 7")
pre = [
    {"title": "P2S configuration", "body": ["Tenant and Issuer carry the same <tenant-id>, trailing slash kept; audience is the Azure VPN Client application ID"], "icon": "gear-box", "accent": C.gold, "badge": "4"},
    {"title": "Admin consent", "body": ["Granted once by a Global Administrator; the app then appears under Enterprise applications"], "icon": "shield-check", "accent": C.purple, "badge": "5"},
    {"title": "Profile distribution", "body": ["azurevpnconfig.xml from the AzureVPN folder over an access-controlled channel; any P2S change means redistributing"], "icon": "download", "accent": C.blue, "badge": "6"},
    {"title": "NSG on the VM subnet", "body": ["3389 allowed from the client pool only; no inbound rule from the internet"], "icon": "firewall", "accent": C.green, "badge": "7"},
]
d.card_col(938, 140, 294, 86, pre, gap=8, body_size=11)

# bottom: where it breaks
d.zone(32, bottom + 14, 1216, 118, "Where it breaks, by message", icon="warning", note="the troubleshooting table, placed on the sequence")
br = [
    {"title": "AADSTS90008 at sign-in", "body": ["consent never granted: step 5"], "accent": C.purple, "icon": "x-circle"},
    {"title": "\"Invalid IP or CIDR\" on save", "body": ["Tenant and Issuer hold different IDs, or a placeholder was left in"], "accent": C.gold, "icon": "x-circle"},
    {"title": "Connected, but RDP fails", "body": ["wrong private IP, VM stopped, or no 3389 rule from the pool"], "accent": C.green, "icon": "x-circle"},
    {"title": "Profile stopped working", "body": ["P2S settings changed; re-download and redistribute"], "accent": C.blue, "icon": "x-circle"},
]
d.card_row(48, bottom + 54, 290, 66, br, gap=12, body_size=11, shadow=False)

d.note_bottom("Every connection is recorded twice: gateway diagnostic logs and Entra sign-in logs. Controls: AC-17, IA-2(1), SC-8 (TLS tunnel), AU-2 and AU-12.")
d.render(repo_path("azure-procedures/diagrams/sop-az-004-3.svg"))
