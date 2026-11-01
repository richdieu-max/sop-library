import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("An ARM request meets Azure Policy: deny, modify and audit",
            "Every create or update is checked against the assignments inherited from the product root; the effect decides whether it is refused, changed on the way in, or let through and recorded.",
            height=680)

# ---- left: the request
d.zone(32, 100, 250, 300, "The request", icon="arrows-lr", note="any route")
for i, (t, b) in enumerate([("Portal", "learn, review, emergency fix"), ("PowerShell / CLI", "the template, SOP-01"), ("Bicep", "configuration as code")]):
    d.card(46, 140 + i * 56, 222, 46, t, [b], accent=C.grey, shadow=False, title_size=12.5, body_size=11)
d.card(46, 310, 222, 78, "Resource Manager", ["receives the request and asks Policy before anything is created"], icon="cloud", accent=C.blue, shadow=False, body_size=11)
d.arrow([(282, 349), (318, 349)], C.blue)

# ---- middle: evaluation
d.zone(320, 100, 420, 300, "Policy evaluation", icon="policy-shield", note="inherited down the tree")
d.card(334, 140, 392, 60, "Assignments at <org>-<product> (the root)", ["Platform, Landing Zones, Customers and Sandbox inherit every one of them; nothing is assigned lower unless written down"], accent=C.blue, shadow=False, body_size=11)
d.text(334, 228, "Each assignment carries one effect:", 12, 600, C.ink)
effects = [("Deny", "refuses the request at Resource Manager", C.red, "guardrail"),
           ("Modify", "changes the request on the way in", C.gold, "guardrail"),
           ("Audit", "lets it through and records it", C.teal, "benchmark")]
for i, (t, b, col, pl) in enumerate(effects):
    yy = 240 + i * 50
    d.card(334, yy, 392, 42, t, [], accent=col, shadow=False, title_size=12.5, pill=(pl, col))
    d.text(400, yy + 22, b, 11.5, 400, C.grey)

# ---- right: outcomes
d.zone(762, 100, 486, 300, "What happens", icon="check-circle")
d.card(776, 140, 458, 78, "Refused: RequestDisallowedByPolicy", ["Nothing is created. Used for allowed regions, no public IP on a NIC, and a required tag on resource groups (deny on the group, not every resource, or OS disks and private-endpoint NICs get blocked too)"], accent=C.red, shadow=False, body_size=11)
d.card(776, 226, 458, 78, "Changed, then created", ["Tags inherited from the resource group onto every resource. Needs a managed identity on the assignment with Tag Contributor, and a remediation task for resources that already exist"], accent=C.gold, shadow=False, body_size=11)
d.card(776, 312, 458, 78, "Created, and marked non-compliant", ["CIS, NIST SP 800-53, ISO 27001, HIPAA and PCI initiatives in Audit: the compliance view and its CSV export are the evidence, not a blocker"], accent=C.teal, shadow=False, body_size=11)
for i, (col, oy) in enumerate([(C.red, 179), (C.gold, 265), (C.teal, 351)]):
    ry = 261 + i * 50
    d.arrow([(726, ry), (744 + i * 6, ry), (744 + i * 6, oy), (776, oy)], col, sw=1.5)

# ---- bottom: guardrail vs benchmark, and reading a deny
d.callout(32, 428, 598, 132, "Guardrails and benchmarks are different numbers", kind="info", icon="heatmap",
          body=["Deny and Modify enforce. A resource that breaks one is drift and must read 100 percent compliant at the root (the exit check).",
                "Audit initiatives score the build against a benchmark; their findings are expected, exported to CSV and taken to the risk register. One real drift problem must never hide under dozens of benchmark rows."])
d.callout(650, 428, 598, 132, "When a Deny hits you", kind="warn", icon="doc-search",
          body=["Read the policies property of the activity log event before touching any guardrail. A Deny often looks like a region block or a quota problem; most often a required tag is missing on a new resource group.",
                "Modify never adds tags when the assignment identity lacks Tag Contributor at the root or no remediation task ran."])
d.chips(32, 578, [("Deny · refuse", C.red), ("Modify · change", C.gold), ("Audit · record", C.teal), ("root scope, inherited", C.blue)])
d.note_bottom("Exit check: Deny assignments at 100 percent compliance at the product root; initiatives exported to CSV. Controls: CM-2, CM-6, CM-7 (configuration baseline and least functionality).")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-101-3.svg"))
