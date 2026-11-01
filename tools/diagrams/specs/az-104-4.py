import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("PIM activation: eligible to active, time-boxed and audited",
            "A member of the owners group holds nothing until activation; MFA, a justification and an approval stand between the request and an Owner role that expires on its own.",
            height=800)

actors = [("Eligible member of sg-az-…-owners", "user", C.blue), ("Privileged Identity Management", "key", C.purple),
          ("Conditional Access", "shield-check", C.teal), ("Approver", "id-card", C.gold), ("Azure RBAC at the product root", "hierarchy", C.red)]
msgs = [
    (0, 1, "Activate Owner: duration (max 4 h) and written justification", C.blue, False),
    (1, 2, "MFA required by the role setting", C.purple, False),
    (2, 0, "prompt: multifactor authentication on the named account", C.teal, False),
    (0, 2, "MFA satisfied (break-glass accounts are the only exclusion)", C.blue, False),
    (1, 3, "approval request with the justification", C.purple, False),
    (3, 1, "approve or deny, recorded with name and time", C.gold, True),
    (1, 4, "active Owner assignment written, expiry set at T + 4 h", C.purple, False),
    (4, 4, "roleAssignments/write lands in the activity log", C.red, False),
    (1, 4, "T + 4 h: assignment removed automatically", C.purple, True),
]
bottom = d.sequence(32, 100, 1216, actors, msgs, lane_h=36)

# ---- settings per role and the licence rule
y0 = bottom + 16
d.zone(32, y0, 596, 188, "Role settings that drive the sequence", icon="gear-box", note="PIM › Azure resources › Settings")
d.card(46, y0 + 40, 280, 64, "Owner (owners group)", ["eligible; max 4 h; MFA, justification and approval required"], accent=C.red, shadow=False, title_size=12.5, body_size=11, pill=("PIM", C.red))
d.card(338, y0 + 40, 276, 64, "Contributor on Customers", ["customer-ops; eligible; max 8 h; MFA and justification"], accent=C.gold, shadow=False, title_size=12.5, body_size=11, pill=("PIM", C.gold))
d.card(46, y0 + 112, 280, 64, "Standing roles", ["platform-ops Contributor on Platform; security and auditors Reader at the root"], accent=C.teal, shadow=False, title_size=12.5, body_size=11, pill=("no activation", C.teal))
d.card(338, y0 + 112, 276, 64, "What never appears", ["a user holding Owner or User Access Administrator directly: a finding"], accent=C.grey, shadow=False, title_size=12.5, body_size=11, pill=("finding", C.red))

d.callout(652, y0, 596, 188, "No P2 licence, no eligibility: record it, never work around it", kind="warn", icon="certificate",
          body=["Eligible assignments need Entra ID P2. If the assignment fails with AadPremiumLicenseRequired, record the missing licence as a finding and do not quietly fall back to standing Owner.",
                "Conditional Access needs P1. Start the MFA policy in Report-only for a week to catch service accounts and old clients, then switch it On; group changes take effect after the cached token expires or a fresh sign-in."])

d.note_bottom("Verify: the PIM export lists Owner and Contributor as eligible, not active; the Conditional Access export shows MFA On and legacy authentication blocked. Controls: AC-6, IA-2, IA-5; HIPAA 164.312(d).")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-104-4.svg"))
