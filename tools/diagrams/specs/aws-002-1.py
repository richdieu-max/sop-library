import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Hardened EC2 in one approved region: no public IP, Session Manager in, everything in-region",
            "Two instances in private subnets behind a load balancer; admins arrive through Systems Manager, and an SCP refuses every other region.",
            height=712, accent=C.gold, vendor="AWS")

d.zone(32, 100, 1216, 460, "Region eu-central-1 (Frankfurt) · VPC 10.30.0.0/16", icon="globe", note="SCP: every other region denied", stroke=C.teal, dashed=True, title_color=C.teal)
d.card(52, 150, 230, 92, "Administrator", ["Identity Center sign-in with MFA", "No key pair, no VPN"], icon="user", accent=C.blue, badge="1")
d.card(52, 270, 230, 92, "Session Manager", ["Shell or RDP through SSM", "Every session logged"], icon="terminal-blue", accent=C.blue, badge="2")
d.arrow([(167, 242), (167, 270)], C.blue)
d.card(52, 390, 230, 92, "Users (HTTPS)", ["Reach only the load balancer"], icon="users", accent=C.green)

d.zone(306, 140, 280, 380, "Public subnets", icon="ports-blue")
d.card(322, 380, 248, 100, "Application Load Balancer", ["443 from the internet", "Targets: the two instances"], icon="arrows-lr", accent=C.green)
d.arrow([(282, 436), (322, 436)], C.green)

d.zone(610, 140, 340, 380, "Private subnets, AZ a and b", icon="lock")
d.card(626, 180, 308, 100, "web-prd-euc1-01  (AZ a)", ["IMDSv2 required · no public IP", "EBS encrypted with KMS key"], icon="server", accent=C.gold, pill=("private", C.green))
d.card(626, 296, 308, 100, "web-prd-euc1-02  (AZ b)", ["Same build, second zone", "Instance profile: SSM + CloudWatch"], icon="server", accent=C.gold, pill=("private", C.green))
d.card(626, 412, 308, 88, "VPC interface endpoints", ["ssm, ssmmessages, ec2messages, logs, kms"], icon="link", accent=C.blue)
d.arrow([(570, 430), (598, 430), (598, 240), (626, 240)], C.green)
d.arrow([(282, 316), (612, 316), (612, 456), (626, 456)], C.blue, dashed=True)

d.zone(974, 140, 254, 380, "Same region only", icon="shield-check")
d.card_col(990, 180, 222, 72, [
    {"title": "AWS Backup", "body": ["Daily by tag, locked vault"], "icon": "refresh-green"},
    {"title": "KMS key", "body": ["alias/ebs-prd-euc1, rotation on"], "icon": "key"},
    {"title": "CloudWatch", "body": ["Agent logs and metrics"], "icon": "chart-monitor"},
    {"title": "Patch Manager", "body": ["Baseline and window"], "icon": "wrench"},
], gap=12)

d.callout(32, 578, 1216, 62, "Wizard defaults: a default subnet assigns a public IP, and the suggested security group allows SSH from 0.0.0.0/0. Steps 3 to 6 change both.", kind="warn")
d.note_bottom("2 AZs, 0 public IPs on instances, 0 inbound admin ports. Controls supported: SC-7, AC-17, SC-28, SC-12, CM-6, CP-9, SA-9(5).")
d.render(repo_path("aws-procedures/diagrams/sop-aws-002-1.svg"))
