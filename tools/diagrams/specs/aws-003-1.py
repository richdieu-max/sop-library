import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("AWS Client VPN with Identity Center: sign in with MFA, reach only your group's networks",
            "The endpoint lives in private subnets; each connection authenticates through SAML and each group is authorised for specific CIDRs only.",
            height=704, accent=C.gold, vendor="AWS")

d.zone(32, 100, 300, 460, "Laptop", icon="laptop")
d.card(48, 140, 268, 90, "AWS-provided client", ["Profile (.ovpn) from IT", "Opens the browser to sign in"], icon="app-window", accent=C.blue, badge="1")
d.card(48, 250, 268, 110, "Client address", ["From the client CIDR 172.20.0.0/22", "Outside the VPC, never overlapping home or office"], icon="ip-server", accent=C.blue)
d.card(48, 380, 268, 90, "Split tunnel", ["Only VPC routes use the tunnel"], icon="arrows-lr", accent=C.blue)

d.zone(356, 100, 300, 460, "IAM Identity Center", icon="entra-user")
d.card(372, 140, 268, 90, "Sign-in with MFA", ["Same account as the AWS console"], icon="user", accent=C.purple, badge="2", badge_color=C.purple)
d.card(372, 250, 268, 110, "SAML application client-vpn", ["Subject = email", "memberOf = group IDs", "Assigned groups only"], icon="id-card", accent=C.purple)
d.card(372, 380, 268, 90, "IAM SAML provider", ["Trusts the application's metadata"], icon="certificate", accent=C.purple)
d.arrow([(316, 185), (372, 185)], C.purple)

d.zone(680, 100, 568, 460, "VPC 10.30.0.0/16", icon="globe", stroke=C.purple, title_color=C.purple)
d.card(696, 140, 536, 90, "Client VPN endpoint", ["TLS on UDP 443 · server certificate in ACM · connection log to CloudWatch", "Associated with one private subnet per AZ · security group sg-client-vpn"], icon="lock", accent=C.gold, badge="3", badge_color=C.gold)
d.arrow([(640, 185), (696, 185)], C.gold, label="assertion")
d.text(696, 262, "Authorization rules (one per group and network)", 12.5, 600, C.ink)
rows = [["Access group (ID)", "Network", "Result"], ["vpn-admins", "10.30.0.0/16", "whole VPC"], ["vpn-support", "10.30.20.0/24", "support subnet only"], ["anyone else", "-", "no routes work"]]
d.table(696, 274, [180, 170, 186], rows, row_h=30)
d.card(696, 410, 536, 90, "Private resources", ["Accept traffic from sg-client-vpn on the ports needed; nothing from the internet"], icon="server-stack", accent=C.green, badge="4", badge_color=C.green)

d.callout(32, 576, 1216, 54, "The access group ID in a rule is the Identity Center group ID sent in memberOf, not the group's display name.", kind="note")
d.note_bottom("Client CIDR between /12 and /22, fixed at creation. Session timeout 8 h. Controls supported: AC-17(1), AC-17(2), IA-2(1), IA-8, AC-3, AC-6, AU-12, SC-8.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-003-1.svg"))
