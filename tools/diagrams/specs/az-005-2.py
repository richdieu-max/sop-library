import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Recovery points, retention and the two recovery paths",
            "How often a copy is taken, where it lives and for how long, and which copy a restore starts from when a region is lost or ransomware hits.",
            height=816)

# ---------------- cadence by tier (24-hour strip)
d.zone(32, 100, 1216, 240, "One day of recovery points, by tier", icon="clock", note="RPO: oldest data you can lose · RTO: time to be back")
x0, x1 = 300, 1000
for hr in range(0, 25, 4):
    px = x0 + (x1 - x0) * hr / 24
    d.line(px, 154, px, 312, C.rule, 1)
    d.text(px, 150, f"{hr:02d}:00", 10.5, 400, C.grey, "middle")
tiers = [
    ("Tier 1 · Critical", "databases, operational systems", C.red, "log every 15–30 min", "RPO 15–30 min", "RTO 1 h", 15),
    ("Tier 2 · Important", "application VMs", C.gold, "Veeam image every 4 h", "RPO 4 h", "RTO 4 h", 240),
    ("Tier 3 · Standard", "dev/test, file servers", C.blue, "Veeam image every 4 h", "RPO 4 h", "RTO 8 h", 240),
]
yy = 160
for name, who, col, how, rpo, rto, every in tiers:
    d.card(48, yy, 236, 44, name, [who], accent=col, shadow=False, title_size=12.5, body_size=11)
    d.parts.append(f'<rect x="{x0}" y="{yy + 16}" width="{x1 - x0}" height="12" rx="6" fill="{col}" opacity="0.12"/>')
    m = 0
    while m <= 24 * 60:
        px = x0 + (x1 - x0) * m / (24 * 60)
        if every >= 60:
            d.parts.append(f'<circle cx="{px:.1f}" cy="{yy + 22}" r="5" fill="{col}" stroke="#fff" stroke-width="1.5"/>')
        else:
            d.line(px, yy + 17, px, yy + 27, col, 1)
        m += every
    d.text(x0, yy + 42, how, 10.5, 400, C.grey)
    d.pill(1016, yy + 6, rpo, col)
    d.pill(1126, yy + 6, rto, col, solid=True)
    yy += 56
d.text(x0, 326, "Tier 1 adds near-zero RPO with Site Recovery replication; the log points are the SQL fallback when replication is not in use.", 10.5, 400, C.grey, max_w=940)

# ---------------- retention bars
d.zone(32, 356, 1216, 212, "Where each copy lives, and for how long", icon="refresh-green", note="bar length = retention")
bx0, bx1 = 420, 1100
day = (bx1 - bx0) / 35
for dd in (0, 7, 14, 21, 28, 35):
    px = bx0 + day * dd
    d.line(px, 400, px, 540, C.rule, 1)
    d.text(px, 396, f"day {dd}", 10.5, 400, C.grey, "middle")
rows = [
    ("VM images (Veeam)", "primary-region blob repository, immutable", 14, C.blue, "local"),
    ("VM images (Veeam copy)", "secondary-region repository, paired region, EU", 35, C.darkblue, "off-site"),
    ("SQL in VMs (Azure Backup)", "Recovery Services vault, GRS, immutable (unlocked)", 14, C.purple, "local + GRS"),
    ("Azure SQL Database", "platform automated, geo-redundant", 35, C.teal, "platform"),
]
yy = 404
for name, where, days, col, tag in rows:
    d.text(48, yy + 15, name, 12.5, 600, C.ink)
    d.text(48, yy + 30, where, 10.5, 400, C.grey, max_w=360)
    d.parts.append(f'<rect x="{bx0}" y="{yy + 6}" width="{day * days:.0f}" height="18" rx="4" fill="{col}"/>')
    if days >= 30:
        d.text(bx0 + day * days - 8, yy + 19, f"{days} days", 11, 600, "#fff", "end")
    else:
        d.text(bx0 + day * days + 8, yy + 19, f"{days} days", 11, 600, col)
    d.pill(1130, yy + 4, tag, col)
    yy += 36
d.text(48, 558, "Infrastructure as code and configuration: committed on change; Git history is the local copy and the remote is the off-site copy.", 10.5, 400, C.grey, max_w=1180)

# ---------------- recovery paths
d.zone(32, 578, 596, 172, "Path A · Primary region lost", icon="lightning", fill=C.redtint, stroke=C.red, title_color=C.red)
d.card(48, 618, 180, 116, "Tier 1", ["fail over with Site Recovery to the secondary region"], badge="1", accent=C.red, shadow=False, body_size=11.5)
d.card(242, 618, 180, 116, "Tier 2 and 3", ["restore from the secondary-region repository (35-day copy)"], badge="2", accent=C.red, shadow=False, body_size=11.5)
d.card(436, 618, 176, 116, "Cut over", ["repoint DNS or Front Door; measure RTO against the tier target"], badge="3", accent=C.red, shadow=False, body_size=11.5)
d.arrow([(228, 676), (242, 676)], C.red); d.arrow([(422, 676), (436, 676)], C.red)

d.zone(652, 578, 596, 172, "Path B · Ransomware or corruption", icon="shield-x", fill=C.goldtint, stroke=C.gold, title_color=C.gold)
d.card(668, 618, 180, 116, "Pick the point", ["last clean 4-hour image, or the 15-minute SQL log point"], badge="1", accent=C.gold, shadow=False, body_size=11.5)
d.card(862, 618, 180, 116, "Immutable restore", ["a compromised admin could not have deleted these copies"], badge="2", accent=C.gold, shadow=False, body_size=11.5)
d.card(1056, 618, 176, 116, "Scan, then return", ["malware scan on the restore before it goes back to production"], badge="3", accent=C.gold, shadow=False, body_size=11.5)
d.arrow([(848, 676), (862, 676)], C.gold); d.arrow([(1042, 676), (1056, 676)], C.gold)

d.note_bottom("Monthly: full restore of one workload per tier and a point-in-time SQL restore to a random moment, with measured RTO/RPO recorded. Controls: CP-6, CP-9, CP-10; CSF PR.DS-11, RC.RP-01.")
d.render(repo_path("azure-procedures/diagrams/sop-az-005-2.svg"))
