import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Patch rings for RHEL: errata reach production only after earlier rings ran clean",
            "Red Hat publishes the advisory; ring 0 takes it within a day, ring 1 in the weekly window, ring 2 in the monthly window or an emergency one.",
            height=660, accent=C.red, vendor="Red Hat")

d.card(32, 110, 260, 110, "Red Hat advisory (RHSA)", ["Severity, CVEs, packages", "dnf updateinfo info RHSA-..."], icon="document", accent=C.red, badge="0", badge_color=C.red)
rings = [("Ring 0 · Test", ["dnf-automatic, security, daily", "Lab copies of each role"], C.green, "daily"),
         ("Ring 1 · Non-production", ["Ansible play, weekly window", "Errata at least 3 days old"], C.gold, "weekly"),
         ("Ring 2 · Production", ["Ansible play, monthly window", "Emergency window for critical"], C.red, "monthly")]
for i, (t, b, col, p) in enumerate(rings):
    x = 336 + i * 308
    d.card(x, 110, 288, 110, t, b, icon="server-stack", accent=col, pill=(p, col))
    d.arrow([(x - 44 if i == 0 else x - 20, 165), (x, 165)], col)

d.zone(32, 250, 760, 300, "The patch play, per batch", icon="terminal-blue", note="serial: 2 · max_fail_percentage: 0")
play = [("Apply errata", "dnf name='*' security=true"), ("Reboot?", "only if dnf needs-restarting -r says so"),
        ("Health check", "uri until 200, 10 tries"), ("Next batch", "or stop if any check fails")]
for i, (t, b) in enumerate(play):
    x = 48 + i * 184
    d.card(x, 296, 170, 110, t, [b], badge=str(i + 1), accent=C.blue)
    if i < 3:
        d.arrow([(x + 170, 351), (x + 184, 351)], C.grey)
d.callout(48, 428, 728, 104, "A failed health check stops the play", ["The failed batch is patched and the rest of production is not: fix forward on that batch or roll it back, then continue."], kind="warn")

d.zone(816, 250, 432, 300, "SLA from release to production", icon="clock")
rows = [["Red Hat severity", "SLA"], ["Critical", "7 days (48 h if in CISA KEV)"], ["Important", "30 days"], ["Moderate, low", "Next monthly window"]]
d.table(832, 294, [170, 230], rows, row_h=38, col_colors=[C.ink, None])
d.text(832, 470, "Report: dnf updateinfo summary --security per host,", 11.5, 400, C.grey)
d.text(832, 488, "collected by Ansible, or Insights / Satellite views.", 11.5, 400, C.grey)

d.note_bottom("3 rings, 1 play, 0 unplanned reboots. Controls supported: SI-2, SI-2(2), SI-2(3), CM-3, CM-4; CIS Controls v8 7.3 and 7.4.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-002-1.svg"))
