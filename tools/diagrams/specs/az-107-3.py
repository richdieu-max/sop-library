import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Pressing the test button: how each alert is fired, reversed and proven",
            "SOP-07-alert-test.ps1 makes small reversible changes in a dedicated test resource group; the activity log, the fired-alert list and the mailbox then have to agree on who, what and when.",
            height=820)

# ---- left: the test script, as a timeline of marked actions
d.zone(32, 100, 560, 330, "The test run, in order", icon="terminal", note="dedicated test resource group only")
steps = [("1", "Create the test resource group", "tagged with Owner and Client; nothing else lives in it", C.grey, ""),
         ("2", "Write an NSG (nsg-alerttest)", "Mark 'write-nsg': UTC time and the signed-in account", C.blue, "write-nsg"),
         ("3", "Create, then delete a CanNotDelete lock", "Mark 'del-lock': the delete is the event the lock alert watches", C.red, "del-lock"),
         ("4", "Remove the test resource group", "Mark 'cleanup': the group's own delete must fire its own alert", C.red, "cleanup"),
         ("5", "Export the test log CSV", "Action, UtcTime, By per row; hashed into the manifest at close-out", C.green, "")]
for i, (n, t, b, col, mark) in enumerate(steps):
    y = 140 + i * 56
    d.card(46, y, 532, 48, t, [b], badge=n, badge_color=col, accent=col, shadow=False, title_size=12.5, body_size=10.5)
    if mark:
        d.pill(478, y + 6, mark, col, size=10)
d.text(46, 424, "Each action is harmless and reversed; the run happens only inside a written test window.", 10.5, 400, C.grey, max_w=532)

# ---- right: operations the matching query watches
d.zone(612, 100, 636, 330, "What the matching query (KQL 2) looks for", icon="doc-search", note="AzureActivity · 7 days · Succeeded")
ops = [("/delete", "resource and resource group deletions, including the test group itself", C.red),
       ("locks/", "lock created and deleted; the del-lock mark should sit beside this row", C.red),
       ("roleAssignments/write", "privileged role changes at any scope", C.purple),
       ("policyAssignments", "guardrail assignments changed", C.gold),
       ("policyExemptions", "an exemption is a quiet way around a guardrail", C.gold)]
yy = d.table(626, 140, [170, 440], [["OperationNameValue has", "Why it is watched"]] + [[o, w] for o, w, _ in ops], row_h=28, size=11.5, mono_cols=(0,))
d.text(626, yy + 20, "Projected per row: TimeGenerated, Caller, CallerIpAddress, OperationNameValue, _ResourceId, CorrelationId.", 10.5, 400, C.grey, max_w=610)
d.text(626, yy + 38, "Also in the template set: the guardrail-change scheduled query (severity 1, every 15 minutes), a Key Vault", 10.5, 400, C.grey, max_w=610)
d.text(626, yy + 54, "data-plane access summary, and a query that lists every fired alert with its timestamp for the evidence.", 10.5, 400, C.grey, max_w=610)

# ---- middle band: proof chain
d.zone(32, 452, 1216, 160, "What proves an alert works (all four, per rule)", icon="check-circle")
proof = [("Fired", "Monitor › Alerts shows the rule fired within 5 to 15 minutes of the marked action", "bell", C.red),
         ("Received", "a person in the action group saw the email; the mailbox is confirmed and does not filter it", "chat-dots", C.gold),
         ("Matched", "KQL 2 row with caller, operation and platform UTC time placed beside the test-log time", "doc-check-green", C.green),
         ("Filed", "test log CSV hashed into the manifest; test group removed and its delete is in the log", "hash-doc", C.blue)]
for i, (t, b, ic, col) in enumerate(proof):
    d.card(46 + i * 302, 492, 290, 104, t, [b], icon=ic, accent=col, shadow=False, title_size=12.5, body_size=11)
    if i < 3:
        d.arrow([(336 + i * 302, 544), (348 + i * 302, 544)], C.grey, sw=1.5)

# ---- bottom: when it does not work
d.zone(32, 632, 1216, 120, "When the button does nothing", icon="warning", fill=C.redtint, stroke=C.red, title_color=C.red, dashed=True)
fails = [("Never fires", "operation name typo, wrong scope (subscription versus management group), or the rule is disabled"),
         ("Fires, no email", "action group email never confirmed, or the mailbox filters it"),
         ("Guardrail change missing from the workspace", "the root management group diagnostic setting is missing: set it with the template")]
for i, (t, b) in enumerate(fails):
    d.card(46 + i * 402, 672, 390, 68, t, [b], accent=C.red, shadow=False, title_size=12, body_size=10.5)

d.note_bottom("Times come from the platform in UTC, never a laptop clock (AU-8). Controls: AU-2, AU-3, AU-6, SI-4; ISO A.8.16; HIPAA 164.312(b); 21 CFR Part 11 §11.10(e).")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-107-3.svg"))
