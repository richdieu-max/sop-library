import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("An SELinux denial: four causes, four fixes, and SELinux stays enforcing",
            "Read the AVC record first: source context, target context, class and permission tell you which of the four it is.",
            height=640, accent=C.red, vendor="Red Hat")

d.card(32, 106, 1216, 92, "type=AVC msg=... denied { read } for comm=\"nginx\" name=\"index.html\" scontext=system_u:system_r:httpd_t:s0 tcontext=unconfined_u:object_r:user_home_t:s0 tclass=file",
       ["httpd_t (nginx) was refused read on a file labelled user_home_t: a labelling problem, case A"], icon="doc-search", accent=C.purple, title_size=11.5)
cases = [("A", C.green, "Wrong file label", ["Files copied or moved from a home directory", "semanage fcontext -a -t httpd_sys_content_t", "'/srv/www(/.*)?' then restorecon -Rv /srv/www"]),
         ("B", C.blue, "Non-standard port", ["Service on 8443 instead of 443", "semanage port -a -t http_port_t -p tcp 8443"]),
         ("C", C.gold, "Behaviour off by boolean", ["App connects out to a database", "getsebool -a | grep httpd", "setsebool -P httpd_can_network_connect on"]),
         ("D", C.red, "Genuine policy gap", ["Custom software, no policy yet", "audit2allow -M local_app (review it!)", "semodule -i local_app.pp"])]
for i, (l, col, t, b) in enumerate(cases):
    d.card(32 + i * 308, 222, 296, 170, t, b, badge=l, badge_color=col, accent=col)
d.callout(32, 412, 1216, 110, "Never the fix: setenforce 0 or SELINUX=disabled", ["Permissive mode is a ten-minute test that proves SELinux is the cause. Switch back to enforcing and apply A, B, C or D.",
                                                                                  "Disabling it removes the containment that stops a compromised service reaching everything else."], kind="warn")
d.note_bottom("Find denials: ausearch -m AVC,USER_AVC -ts recent; explain them: sealert -a /var/log/audit/audit.log. Controls supported: AC-3, AC-6, CM-6.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-004-2.svg"))
