import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Apply with Ansible, judge with OpenSCAP: hardening a RHEL group in stages",
            "Scan before, dry-run and stage on one canary, roll out in batches, scan again; every FAIL is fixed or carries a dated exception.",
            height=716, accent=C.red, vendor="Red Hat")

steps = [
    ("Baseline scan", ["evidence.yml before any change, so the improvement can be shown"], "target", C.purple),
    ("Dry run", ["--check --diff on the canary; read SSH, firewalld and PAM diffs"], "doc-search", C.gold),
    ("Stage: ssh, auth", ["Keep the session open; prove a second login and sudo -v"], "lock", C.red),
    ("Stage: the rest", ["Read the reboot message; reboot in the window if needed"], "terminal-blue", C.red),
    ("Group, in batches", ["--limit rhel_web --forks 5"], "server-stack", C.red),
    ("Scan again", ["Same profile, evidence folder per host"], "target", C.purple),
]
for i, (t, b, ic, col) in enumerate(steps):
    x = 32 + i * 206
    d.card(x, 110, 194, 150, t, b, icon=ic, accent=col, badge=str(i + 1), badge_color=col)
    if i < len(steps) - 1:
        d.arrow([(x + 194, 185), (x + 206, 185)], C.grey)

d.zone(32, 290, 600, 280, "Stop conditions", icon="warning")
d.card_col(48, 330, 568, 50, [
    {"title": "The diff touches something you did not expect", "accent": C.red},
    {"title": "You lose the SSH session or sudo on the canary", "accent": C.red},
    {"title": "More than one host fails in a batch", "accent": C.red},
    {"title": "A high-severity rule still fails with no exception", "accent": C.red},
], gap=10)

d.zone(656, 290, 592, 280, "Every FAIL ends one of three ways", icon="check-circle", note="letters mark the alternatives")
d.card_col(672, 330, 560, 70, [
    {"title": "Fix and re-scan", "body": ["A setting the role should own: re-run that tag"], "badge": "A", "badge_color": C.green, "accent": C.green},
    {"title": "Change the role", "body": ["A gap in the baseline: new task, review, release, re-run"], "badge": "B", "badge_color": C.blue, "accent": C.blue},
    {"title": "Dated exception", "body": ["Partition layout, log host, boot password: owner and expiry"], "badge": "C", "badge_color": C.gold, "accent": C.gold},
], gap=10)
d.callout(32, 586, 1216, 52, "Out-of-band console access to the canary is a prerequisite: it is the way back if SSH breaks.", kind="warn")
d.note_bottom("Profile: SCAP Security Guide cis_server_l1. Controls supported: CM-2, CM-6, CM-7, CA-2, CA-7, RA-5.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-001-1.svg"))
