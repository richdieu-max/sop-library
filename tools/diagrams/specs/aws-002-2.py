import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Why IMDSv2, and the three layers that keep data in the region",
            "An SSRF bug can relay a GET to the metadata service; IMDSv2 answers only requests carrying a session token obtained with a PUT, which a relayed GET cannot get.",
            height=680, accent=C.gold, vendor="AWS")

d.zone(32, 100, 740, 470, "A web app with an SSRF bug asks for credentials", icon="warning")
d.text(52, 152, "IMDSv1 (optional tokens)", 12.5, 600, C.ink)
d.card(52, 164, 220, 76, "Attacker", ["?url=http://169.254.169.254/..."], icon="user", accent=C.red, badge="1", badge_color=C.red)
d.card(302, 164, 200, 76, "Vulnerable app", ["Fetches the URL it is given"], icon="app-window", accent=C.red)
d.card(532, 164, 220, 76, "IMDSv1", ["Answers any GET"], icon="server", accent=C.red, pill=("leaks", C.red))
d.arrow([(272, 202), (302, 202)], C.red)
d.arrow([(502, 202), (532, 202)], C.red)
d.text(52, 268, "Role credentials go back to the attacker in the page response.", 12, 400, C.red)

d.text(52, 320, "IMDSv2 (HttpTokens = required)", 12.5, 600, C.ink)
d.card(52, 332, 220, 76, "Attacker", ["Same relayed GET"], icon="user", accent=C.green, badge="2", badge_color=C.green)
d.card(302, 332, 200, 76, "Vulnerable app", ["Cannot add the token header"], icon="app-window", accent=C.green)
d.card(532, 332, 220, 76, "IMDSv2", ["401: no session token"], icon="shield-check", accent=C.green, pill=("refused", C.green))
d.arrow([(272, 370), (302, 370)], C.green)
d.arrow([(502, 370), (532, 370)], C.green)
d.card(52, 430, 700, 118, "How a legitimate client gets in", ["PUT /latest/api/token with a TTL header returns a token; every GET then sends X-aws-ec2-metadata-token.",
                                                                "Hop limit 1 means the PUT response cannot leave the instance; containers on the host need 2.",
                                                                "Set the account default once: aws ec2 modify-instance-metadata-defaults --http-tokens required."], icon="key", accent=C.blue)

d.zone(796, 100, 452, 470, "Residency: three layers", icon="globe", note="all three, not one")
d.card_col(812, 140, 420, 128, [
    {"title": "SCP on the OU", "body": ["Denies any request whose aws:RequestedRegion is not eu-central-1; global services exempt; break-glass role excluded"], "icon": "policy-shield", "accent": C.gold, "badge": "A", "badge_color": C.gold},
    {"title": "Backups and copies stay in-region", "body": ["Backup vault, snapshots and AMI copies in eu-central-1; any DR region must also be inside the residency boundary"], "icon": "refresh-green", "accent": C.gold, "badge": "B", "badge_color": C.gold},
    {"title": "KMS keys are regional", "body": ["A snapshot encrypted with a Frankfurt key cannot be read in another region without a deliberate re-encrypting copy"], "icon": "key", "accent": C.gold, "badge": "C", "badge_color": C.gold},
], gap=12)

d.note_bottom("IMDS answers on 169.254.169.254; tokens last up to 6 hours. Controls supported: CM-6, AC-3, SC-12, SC-28, SA-9(5); CIS AWS Foundations 5.6 (IMDSv2).")
d.render(repo_path("aws-procedures/diagrams/sop-aws-002-2.svg"))
