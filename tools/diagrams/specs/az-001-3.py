import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Day zero in order: five steps, each leaving evidence an auditor can open",
            "The steps run in this order because each one protects the next; the lower row is where the proof of each step lives in the portal afterwards.",
            height=690)

cols = [48 + i * 240 for i in range(5)]
W = 224

steps = [
    ("Create the tenant", ["Organisation name, initial domain, country; record the tenant ID; private browser window if signed in elsewhere"], "hierarchy", C.blue),
    ("Emergency accounts", ["Two cloud-only Global Administrators on onmicrosoft.com, FIDO2 keys or long random passwords stored offline, excluded from every CA policy by a named group"], "breakglass", C.red),
    ("MFA for everyone", ["Security Defaults for a small tenant; otherwise Conditional Access: MFA for all users, legacy auth blocked, phishing-resistant MFA for admins"], "shield-check", C.purple),
    ("Custom domain", ["Add the domain, create the MS= TXT record at the registrar, verify once DNS has propagated"], "globe", C.teal),
    ("Groups and policy", ["Build the hierarchy, move subscriptions under it, assign allowed locations, no public IP on NICs, required tags and a benchmark initiative in audit mode at org root"], "policy-shield", C.green),
]
evidence = [
    ("Audit logs", ["Entra ID › Audit logs, activity \"Create tenant\""]),
    ("Role assignments", ["Entra ID › Roles and administrators › Global Administrator › Assignments"]),
    ("Policies", ["Entra ID › Security › Conditional Access › Policies, or the Security Defaults setting"]),
    ("Status: Verified", ["Entra ID › Custom domain names › Status column"]),
    ("Policies, compliance", ["Management groups › org root › Policies, and the compliance view"]),
]

d.zone(32, 100, 1216, 196, None)
d.text(44, 118, "Steps, in the order they protect each other", 12.5, 600, C.grey)
for i, (title, body, ic, col) in enumerate(steps):
    d.card(cols[i], 130, W, 150, title, body, icon=ic, accent=col, badge=str(i + 1), badge_color=col, body_size=11.5)
    if i < 4:
        d.arrow([(cols[i] + W, 205), (cols[i + 1], 205)], C.grey, sw=1.6)
# evidence row
for i, (title, body) in enumerate(evidence):
    col = steps[i][3]
    d.arrow([(cols[i] + W / 2, 282), (cols[i] + W / 2, 328)], col, sw=1.6, dashed=True)
    d.card(cols[i], 332, W, 88, title, body, icon="doc-check-green", accent=col, shadow=False, body_size=11)

# gates
d.zone(32, 444, 1216, 150, "Gates the order enforces", icon="pause", note="each gate is a sentence from the steps")
gates = [
    {"title": "Before step 3", "body": ["Emergency accounts exist and are excluded from CA, so an MFA mistake cannot lock the tenant"], "icon": "breakglass", "accent": C.red},
    {"title": "Inside step 3", "body": ["Never leave a gap between turning Security Defaults off and turning Conditional Access on"], "icon": "hourglass", "accent": C.purple},
    {"title": "Inside step 4", "body": ["Verify only after the TXT record has propagated; a failed check is a wait, not a fault"], "icon": "clock", "accent": C.teal},
    {"title": "After step 5", "body": ["Only now does the first resource get deployed: policy at org root is already watching"], "icon": "check-circle", "accent": C.green},
]
d.card_row(48, 484, 290, 96, gates, gap=12, body_size=11.5)

d.note_bottom("Five steps, five evidence locations, four gates. Any sign-in by an emergency account raises an alert. Controls: AC-2, IA-2(1), CP-2, CM-2, PL-8.")
d.render(repo_path("azure-procedures/diagrams/sop-az-001-3.svg"))
