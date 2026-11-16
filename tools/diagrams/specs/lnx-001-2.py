import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("From one OpenSCAP rule result to a closed finding",
            "The ARF file holds the result; the SCAP Security Guide benchmark in the same file holds the title, severity and NIST references.",
            height=600, accent=C.red, vendor="Red Hat")

d.card(32, 110, 380, 150, "rule-result in the ARF", ["idref ...content_rule_sshd_disable_root_login", "result: fail", "severity: medium"], icon="code-braces", accent=C.purple, badge="1", badge_color=C.purple, mono_body=True)
d.card(450, 110, 380, 150, "Rule in the benchmark", ["title: Disable SSH Root Login", "reference (800-53): AC-6(2), AC-17(a), IA-2", "CIS reference kept separate"], icon="document", accent=C.purple, badge="2", badge_color=C.purple)
d.arrow([(412, 185), (450, 185)], C.purple)
d.card(868, 110, 380, 150, "Finding in report.md", ["FAIL · SSH · Disable SSH Root Login", "NIST: AC-6(2), AC-17(a), IA-2"], icon="list-blue", accent=C.red, badge="3", badge_color=C.red)
d.arrow([(830, 185), (868, 185)], C.red)

d.text(32, 300, "Status mapping", 13.5, 600, C.ink)
rows = [["oscap result", "Severity", "Finding", "Listed in report.md"],
        ["fail", "high or medium", "FAIL", "yes"],
        ["fail", "low or unknown", "WARN", "yes"],
        ["error, unknown", "any", "WARN (could not evaluate)", "yes"],
        ["pass, fixed", "any", "PASS", "findings.json only"],
        ["notapplicable, notselected, notchecked", "any", "counted, not a finding", "count in the header"]]
d.table(32, 314, [380, 200, 300, 336], rows, row_h=34, col_colors=[C.ink, None, None, None])

d.note_bottom("Exit code 2 from oscap means rules failed: a result, not an error. Controls supported: CA-2, CA-7, RA-5, AU-9 (SHA-256 manifest).")
d.render(repo_path("linux-administration/diagrams/sop-lnx-001-2.svg"))
