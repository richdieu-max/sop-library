import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("An AD user signs in over SSH: the path, and where it breaks",
            "Six hops from sshd to a sudo prompt; each failure mode has one command that shows it.",
            height=720, accent=C.red, vendor="Red Hat")

actors = [("sshd + PAM", "terminal", C.red), ("SSSD", "gear", C.blue), ("Domain controller", "server-stack", C.purple), ("sudo", "lock", C.gold)]
msgs = [(0, 1, "1  pam_sss: authenticate jdoe", C.red, False),
        (1, 2, "2  Kerberos AS-REQ with the password", C.purple, False),
        (2, 1, "3  Ticket, if password and clock are good", C.purple, True),
        (1, 2, "4  LDAP: jdoe's groups", C.blue, False),
        (1, 0, "5  Access check: group in realm permit list?", C.blue, True),
        (0, 3, "6  sudo: %GG-Linux-Web-Admins rule matches", C.gold, False)]
yy = d.sequence(32, 100, 1216, actors, msgs, lane_h=44)

d.zone(32, yy + 18, 1216, 170, "Failure, cause, and the command that shows it", icon="warning")
fails = [("2-3", "Clock skew", "chronyc tracking"), ("1-2", "No domain found", "dig -t SRV _ldap._tcp.ad.contoso.com"),
         ("4", "No such user", "sssctl domain-status ad.contoso.com"), ("5", "Permission denied", "realm list; sss_cache -E"),
         ("6", "Not in sudoers", "sudo -l -U jdoe")]
for i, (s, t, cmd) in enumerate(fails):
    d.card(48 + i * 240, yy + 58, 228, 110, f"Step {s}: {t}", [cmd], accent=C.red)
d.note_bottom("Every refusal is logged in /var/log/secure with the user's real AD identity. Controls supported: IA-2, AC-3, AC-6, AU-3.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-003-2.svg"))
