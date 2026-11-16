import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Three ways back: which recovery path, how fast, and what to repoint",
            "Pick the path by tier; every path ends with traffic moved to the recovered resource, which is the step drills most often forget.",
            height=640, accent=C.gold, vendor="AWS")

paths = [
    ("A", C.gold, "AWS Backup restore", ["Any protected resource", "Same region or the recovery region", "Clock: hours (data size)", "Triggered by: backup operator"]),
    ("B", C.red, "EDR recovery launch", ["Tier-1 servers", "Launch from the latest point in time", "Clock: minutes", "Triggered by: incident commander"]),
    ("C", C.blue, "RDS point-in-time restore", ["Databases", "From replicated automated backups", "Clock: minutes to hours", "Triggered by: DBA"]),
]
for i, (letter, col, title, body) in enumerate(paths):
    d.card(32 + i * 412, 110, 392, 170, title, body, badge=letter, badge_color=col, accent=col)
    d.arrow([(228 + i * 412, 280), (228 + i * 412, 316)], col)

d.zone(32, 318, 1216, 220, "Then repoint, or recovery is not finished", icon="refresh-green")
d.card_row(48, 360, 286, 150, [
    {"title": "DNS", "body": ["Route 53 records or failover routing to the recovered endpoints; low TTL set in advance"], "icon": "globe", "badge": "1"},
    {"title": "Load balancer targets", "body": ["Register the recovered instances; health checks must pass before traffic moves"], "icon": "arrows-lr", "badge": "2"},
    {"title": "Connection strings", "body": ["Applications point at the restored database endpoint (Secrets Manager value updated)"], "icon": "key", "badge": "3"},
    {"title": "Fail back later", "body": ["EDR reverses replication; backups restore into the primary when it returns"], "icon": "sync-purple", "badge": "4"},
], gap=12)
d.note_bottom("Measure each drill from the decision to recover to the first successful application request. Controls supported: CP-10, CP-4, IR-4.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-004-2.svg"))
