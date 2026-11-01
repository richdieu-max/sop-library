import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Build order: what each layer gives the next",
            "Five layers, built in this order by the template; each one is the scope or the record the next one depends on, and each has its own exit check.",
            height=740)

cols = [
    dict(n="1", title="Management groups", icon="hierarchy", col=C.blue,
         builds=["Product root <org>-<product>, then Platform, Landing Zones (with Customers below) and Sandbox; the subscription moved under Customers"],
         gives="One scope where policy and roles are set once and inherited by everything built later",
         verify="Get-AzManagementGroup -Expand -Recurse shows the five groups and the subscription under Customers"),
    dict(n="2", title="Groups and RBAC", icon="users", col=C.purple,
         builds=["Five sg-az security groups (owners, platform-ops, customer-ops, security, auditors), each with an owner; roles assigned to groups at the root"],
         gives="Roles belong to teams, not people: removing a person from a group removes everything",
         verify="Role assignments at the root are held by groups only; export and hash"),
    dict(n="3", title="Guardrails at the root", icon="policy-shield", col=C.red,
         builds=["Deny: allowed regions, no public IP on a NIC, required tag on resource groups. Modify: inherit tags (managed identity). Audit: CIS, NIST, ISO, HIPAA, PCI initiatives"],
         gives="Every later resource is checked on the way in; benchmarks produce evidence rather than blocking",
         verify="Policy › Compliance at the root: Deny assignments at 100 percent; initiatives exported to CSV"),
    dict(n="4", title="Central logging", icon="list-blue", col=C.teal,
         builds=["Log Analytics workspace (365 days); GRS storage with am-* containers under a time-based WORM policy, unlocked; subscription and root-group activity logs streamed"],
         gives="A searchable working window plus a seven-year regulatory record that nobody can shorten",
         verify="Containers show a time-based retention policy, unlocked; management-group events arrive in the workspace"),
    dict(n="5", title="Hub network, locks", icon="globe", col=C.gold,
         builds=["Hub VNet with snet-mgmt, snet-appgw and the reserved AzureFirewallSubnet and AzureBastionSubnet; Delete locks on the platform and hub resource groups"],
         gives="The one network every customer spoke peers with, and a floor under accidental deletion",
         verify="Evidence manifest records run ID, operator and UTC time (ALCOA+)"),
]
x = 32; w = 228; gap = 19
for i, c in enumerate(cols):
    cx = x + i * (w + gap)
    d.zone(cx, 100, w, 426, None, fill=C.zone)
    d.badge(cx + 22, 124, c["n"], c["col"], r=12, size=12)
    d.icon(cx + 40, 112, c["icon"], 0.5)
    d.text(cx + 72, 129, c["title"], 13, 600, C.ink, max_w=w - 80)
    d.card(cx + 10, 148, w - 20, 150, "What it builds", c["builds"], accent=c["col"], shadow=False, title_size=12.5, body_size=11)
    d.card(cx + 10, 308, w - 20, 92, "What the next layer gets", [c["gives"]], accent=c["col"], shadow=False, title_size=12.5, body_size=11)
    d.card(cx + 10, 410, w - 20, 104, "Exit check", [c["verify"]], accent=C.green, shadow=False, title_size=12.5, body_size=11, pill=("verify", C.green))
    if i < len(cols) - 1:
        d.arrow([(cx + w, 354), (cx + w + gap, 354)], C.grey, sw=2)

d.callout(32, 546, 598, 118, "The template is the version of record", kind="info", icon="code-braces",
          body=["SOP-01-landing-zone.ps1 is idempotent: a rerun converges and never duplicates. Every client value lives in tenant.parameters.json (never in a public repository). Run with -WhatIf first to list every change, then build, then Get-AzPolicyStateSummary as the exit check."])
d.callout(650, 546, 598, 118, "Rollback runs the order in reverse", kind="warn", icon="refresh-green",
          body=["Locks, resource groups, policy assignments, role assignments, then management groups (move the subscription back to the tenant root first). Never delete the archive storage account: an unlocked WORM policy still blocks deleting the data inside it until the retention ends."])
d.note_bottom("Exit criterion: every subscription under the product root and Deny guardrails at 100 percent. Controls: CM-2, CM-7 (baseline and guardrails), AC-2 (group-based roles), AU-6, AU-9 (central and protected logs).")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-101-2.svg"))
