import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Two regions, locked vaults, and a warm path for tier 1",
            "AWS Backup copies every recovery point to a locked vault in the recovery region; Elastic Disaster Recovery keeps tier-1 servers replicating continuously.",
            height=716, accent=C.gold, vendor="AWS")

d.zone(32, 100, 520, 470, "Primary region eu-central-1", icon="globe", stroke=C.teal, dashed=True, title_color=C.teal)
d.card(300, 140, 236, 90, "Tier 1 servers", ["Tag Backup=tier1", "EDR agent installed"], icon="server-stack", accent=C.red, pill=("tier 1", C.red))
d.card(48, 140, 236, 90, "Tier 2 servers", ["Tag Backup=daily"], icon="server", accent=C.gold, pill=("tier 2", C.gold))
d.card(300, 250, 236, 90, "RDS database", ["Automated backups, PITR", "Cross-region replication on"], icon="sql", accent=C.blue)
d.card(48, 250, 236, 90, "Backup plan plan-prd", ["Daily 35 d · monthly 1 y", "Assigned by tag"], icon="calendar", accent=C.gold)
d.card(48, 380, 488, 100, "vault-prd-euc1 (locked)", ["Encrypted with the Frankfurt KMS key", "Vault Lock: governance first, compliance after a passed restore test"], icon="lock", accent=C.green, pill=("locked", C.green))
d.arrow([(166, 340), (166, 380)], C.gold)
d.card(48, 494, 488, 60, "Failure alerts", ["BACKUP_, COPY_ and RESTORE_JOB_FAILED to SNS"], icon="bell", accent=C.blue)

d.zone(728, 100, 520, 470, "Recovery region eu-west-1", icon="globe", stroke=C.teal, dashed=True, title_color=C.teal)
d.card(744, 380, 488, 100, "vault-dr-euw1 (locked)", ["Copies re-encrypted with the Dublin KMS key", "Same retention as the source rule"], icon="lock", accent=C.green, pill=("locked", C.green))
d.card(744, 140, 488, 100, "EDR staging area", ["Continuous block replication, TCP 1500", "Point-in-time snapshots kept 7 days; launch settings ready"], icon="sync-purple", accent=C.red)
d.card(744, 260, 488, 90, "RDS automated backups (replicated)", ["Point-in-time restore available if the primary region is lost"], icon="db-globe", accent=C.blue)

d.arrow([(536, 430), (744, 430)], C.green, label="copy job, every rule")
d.arrow([(536, 185), (744, 185)], C.red, label="seconds RPO")
d.arrow([(536, 300), (744, 300)], C.blue, label="replicated backups")

d.callout(32, 586, 1216, 56, "Restore testing (weekly) and EDR drills (quarterly) are what turn the RPO and RTO targets into measured numbers.", kind="ok")
d.note_bottom("Tier 1: RPO seconds, RTO minutes. Tier 2: RPO 24 h, RTO hours. Controls supported: CP-9, CP-9(1), CP-6, CP-7, CP-10, SI-7.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-004-1.svg"))
