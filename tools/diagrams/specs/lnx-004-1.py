import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("RHEL triage order: the fastest path from 'it is down' to the cause",
            "Work down the steps; most faults show up in the first four. Each step names the command and the cause most often found there.",
            height=720, accent=C.red, vendor="Red Hat")

steps = [("Service running?", "systemctl status · journalctl -u -b", "Unit failed: bad path (203/EXEC) or app error"),
         ("Listening, and where?", "ss -tlnp", "Bound to 127.0.0.1 only"),
         ("Can traffic reach it?", "firewall-cmd --list-all · ip route get", "Port not allowed in the active zone"),
         ("SELinux saying no?", "ausearch -m AVC -ts recent", "Wrong file context or a non-standard port"),
         ("Disk, memory, load?", "df -hT · df -i · free -h · lsof +L1", "Full /var or deleted files held open"),
         ("Names and time?", "dig · getent hosts · chronyc tracking", "Resolver or clock offset"),
         ("What changed?", "dnf history · rpm -V", "A package update the night before")]
for i, (t, cmd, cause) in enumerate(steps):
    y = 106 + i * 76
    d.card(32, y, 300, 64, t, [], badge=str(i + 1), accent=C.red if i < 4 else C.gold)
    d.card(348, y, 420, 64, cmd, [], icon="terminal-blue", shadow=False, mono_body=True, title_size=12.5)
    d.card(784, y, 464, 64, cause, [], icon="info-card", shadow=False, title_size=12.5)
    if i < len(steps) - 1:
        d.arrow([(182, y + 64), (182, y + 76)], C.grey)
d.note_bottom("Then the application's own logs. Collect a sos report for Red Hat support. Controls supported: IR-4, SI-4, AU-6.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-004-1.svg"))
