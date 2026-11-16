import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Global once, regional everywhere: what each new account needs, and where",
            "Some settings apply to the whole account; detectors and defaults are regional and must be repeated in every region the account will use.",
            height=640, accent=C.gold, vendor="AWS")

d.zone(32, 100, 380, 450, "Which kind of account?", icon="question-diamond-gold", note="letters mark the alternatives")
d.card(48, 140, 348, 120, "Standalone account", ["Root lockdown by hand (steps 1-5)", "Detectors enabled by you in each region", "Identity Center in the account itself"], badge="A", badge_color=C.gold, accent=C.gold)
d.card(48, 276, 348, 140, "Member of an AWS Organization", ["Root credentials removed centrally", "Delegated administrator auto-enables", "GuardDuty, Security Hub and Config", "Region guardrail by SCP (SOP-AWS-002)"], badge="B", badge_color=C.blue, accent=C.blue, pill=("preferred", C.green))
d.card(48, 432, 348, 100, "Either way", ["Run aws-posture-check before the first workload and keep the evidence folder"], icon="hash-doc", accent=C.green)

d.zone(436, 100, 812, 450, "Scope of each setting", icon="globe")
rows = [["Setting", "Scope", "How often"],
        ["IAM Identity Center", "Account / Organization, home region", "Once"],
        ["CloudTrail trail", "Multi-region trail, one bucket", "Once"],
        ["S3 Block Public Access", "Account (s3control)", "Once"],
        ["IAM password policy", "Account (only if IAM users exist)", "Once"],
        ["Alternate contacts, budget", "Account", "Once"],
        ["GuardDuty detector", "Region", "Every used region"],
        ["Security Hub", "Region", "Every used region"],
        ["AWS Config recorder", "Region (global resources in home region only)", "Every used region"],
        ["IAM Access Analyzer", "Region", "Every used region"],
        ["EBS encryption by default", "Region", "Every used region"]]
d.table(452, 140, [250, 340, 186], rows, row_h=34, col_colors=[C.ink, None, None])
d.note_bottom("5 account-wide settings, 5 regional ones. A region missed here is a region with no threat detection. Controls supported: SI-4, AU-12, CM-8, SC-28.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-001-2.svg"))
