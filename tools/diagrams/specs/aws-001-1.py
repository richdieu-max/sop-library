import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("AWS account day zero: root locked away, people through Identity Center, everything recorded",
            "The baseline applied before the first workload: one identity nobody uses, short-lived access for people, and account-wide logging, detection and safe defaults.",
            height=690, accent=C.gold, vendor="AWS")

d.zone(32, 100, 360, 440, "Root user: locked away", icon="lock", note="steps 1-5")
d.card_col(48, 140, 328, 80, [
    {"title": "Two FIDO2 security keys", "body": ["Registered on root, stored apart under dual control"], "icon": "key", "accent": C.red, "pill": ("MFA", C.green)},
    {"title": "No access keys, ever", "body": ["Root keys cannot be limited by any policy"], "icon": "x-circle", "accent": C.red},
    {"title": "Group mailbox, three contacts", "body": ["Billing, operations and security alternate contacts"], "icon": "users", "accent": C.red},
    {"title": "Centralized root access", "body": ["In an Organization: member accounts lose root credentials"], "icon": "hierarchy", "accent": C.red, "pill": ("org", C.blue)},
], gap=12)

d.zone(416, 100, 400, 440, "People: IAM Identity Center", icon="entra-user", note="steps 6-9")
d.card(436, 140, 360, 70, "Identity Center user", ["MFA every time they sign in"], icon="user", accent=C.blue, badge="1")
d.arrow([(616, 210), (616, 236)], C.blue)
d.card(436, 238, 360, 70, "Group: aws-admins / operators / auditors", ["People are assigned to groups, never to accounts"], icon="users", accent=C.blue, badge="2")
d.arrow([(616, 308), (616, 334)], C.blue)
d.card(436, 336, 360, 70, "Permission set", ["AdministratorAccess 1 h · PowerUser · SecurityAudit"], icon="id-card", accent=C.blue, badge="3")
d.arrow([(616, 406), (616, 432)], C.blue)
d.card(436, 434, 360, 70, "Account 111122223333", ["Temporary role credentials, no IAM users"], icon="cloud", accent=C.blue, badge="4")

d.zone(840, 100, 408, 440, "Record, detect, default", icon="shield-check", note="steps 10-11 + CLI")
items = [("CloudTrail", "multi-region, log validation", "doc-search"), ("GuardDuty", "every used region", "defender-shield"),
         ("Security Hub", "FSBP + CIS standards", "chart-monitor"), ("AWS Config", "recorder per region", "policy-shield"),
         ("Access Analyzer", "external access findings", "target"), ("S3 public block", "Block Public Access, account level", "db-blue"),
         ("EBS encryption", "on by default, every region", "ssd"), ("Budget alarm", "80% and 100%", "dollar")]
for i, (t, b, ic) in enumerate(items):
    col, row = i % 2, i // 2
    d.card(856 + col * 192, 140 + row * 96, 182, 84, t, [b], icon=ic, accent=C.gold)

d.callout(32, 556, 1216, 64, "A cost spike is often the first sign of stolen access keys, which is why the budget alarm is part of the security baseline.", kind="note")
d.note_bottom("Root: 2 keys, 0 access keys. People: 3 groups, sessions of 1 to 4 hours. Controls supported: AC-2, AC-6(5), IA-2(1), AU-2, AU-12, SI-4, SC-28; CIS AWS Foundations 1 to 4.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-001-1.svg"))
