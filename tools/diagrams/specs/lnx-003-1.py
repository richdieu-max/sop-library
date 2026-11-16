import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("RHEL in Active Directory: join once with realmd, then SSSD does the work",
            "DNS finds the domain controllers, realm join creates the computer account and keytab, and SSSD authenticates, resolves groups and caches for offline logins.",
            height=716, accent=C.red, vendor="Red Hat")

d.zone(32, 100, 560, 470, "RHEL server web-prd-01", icon="server", stroke=C.red, dashed=True, title_color=C.red)
d.card(48, 140, 256, 96, "realmd", ["Discovers the domain", "Runs the join once"], icon="search" if False else "doc-search", accent=C.red, badge="1", badge_color=C.red)
d.card(320, 140, 256, 96, "adcli", ["Computer object in the OU", "Keytab /etc/krb5.keytab"], icon="key", accent=C.red, badge="2", badge_color=C.red)
d.card(48, 256, 528, 120, "sssd", ["Authenticates with Kerberos, resolves users and groups over LDAP", "Caches credentials for offline logins",
                                   "Access: simple provider, permitted groups only"], icon="gear", accent=C.blue, badge="3")
d.card(48, 396, 256, 100, "PAM and NSS", ["Set by authselect", "with-mkhomedir for /home/%u"], icon="lock", accent=C.blue)
d.card(320, 396, 256, 100, "sudoers.d/60-ad-admins", ["%GG-Linux-Web-Admins ALL=(ALL) ALL"], icon="terminal", accent=C.gold)
d.card(48, 512, 528, 44, "Local break-glass admin with a key", [], icon="breakglass", accent=C.gold, shadow=False)

d.zone(656, 100, 592, 470, "Active Directory  ad.contoso.com", icon="hierarchy")
d.card(672, 140, 560, 96, "DNS", ["_ldap._tcp and _kerberos._tcp SRV records point at the domain controllers"], icon="globe", accent=C.purple)
d.card(672, 256, 272, 120, "Domain controllers", ["88 Kerberos · 389 LDAP", "464 password · 3268 GC", "Time source for the domain"], icon="server-stack", accent=C.purple)
d.card(960, 256, 272, 120, "OU=Linux,OU=Servers", ["Computer account", "web-prd-01 (15 chars max)"], icon="folder", accent=C.purple)
d.card(672, 396, 560, 100, "Groups", ["GG-Linux-Web-Login: may sign in", "GG-Linux-Web-Admins: may sign in and use sudo"], icon="users", accent=C.green)

d.arrow([(592, 188), (672, 188)], C.purple, label="discover")
d.arrow([(592, 316), (672, 316)], C.blue, label="Kerberos + LDAP")
d.arrow([(592, 446), (672, 446)], C.green, label="membership")

d.callout(32, 586, 1216, 56, "Leavers: disabling the AD account ends access on every joined server at the next login; nothing to clean up per host.", kind="ok")
d.note_bottom("Clock skew limit 5 minutes. Controls supported: AC-2, AC-2(1), AC-3, AC-6, IA-2, IA-5, AU-3.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-003-1.svg"))
