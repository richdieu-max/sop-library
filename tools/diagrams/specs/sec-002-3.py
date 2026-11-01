import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Evidence first: what to export before containment, and where it lives",
            "Containment destroys evidence: removing a rule deletes its definition and resetting MFA removes the attacker's method, so everything is exported and hashed before step 1.",
            height=820)

# ---------------- three source zones (left)
zx, zw = 32, 560
d.zone(zx, 100, zw, 214, "Exchange Online", icon="folder-share", note="ExchangeOnlineManagement v3")
d.card(zx + 16, 140, 258, 78, "Inbox rules, hidden included", ["Get-InboxRule -IncludeHidden; also Outlook on the web and Sweep"], icon="list-blue", accent=C.blue, shadow=False, body_size=11)
d.card(zx + 290, 140, 254, 78, "Forwarding", ["ForwardingAddress, ForwardingSmtpAddress, DeliverToMailboxAndForward"], icon="arrows-lr", accent=C.blue, shadow=False, body_size=11)
d.card(zx + 16, 228, 258, 64, "Mailbox permissions", ["FullAccess, SendAs, SendOnBehalf, calendar delegates"], icon="users", accent=C.blue, shadow=False, body_size=11)
d.card(zx + 290, 228, 254, 64, "Message trace", ["what the account sent, to whom, and when"], icon="chat-dots", accent=C.blue, shadow=False, body_size=11)

d.zone(zx, 330, zw, 214, "Entra ID (Microsoft Graph)", icon="entra-user", note="Microsoft.Graph on a clean admin workstation")
d.card(zx + 16, 370, 258, 78, "Authentication methods", ["Get-MgUserAuthenticationMethod; any method the user did not register"], icon="key", accent=C.purple, shadow=False, body_size=11)
d.card(zx + 290, 370, 254, 78, "OAuth grants", ["Get-MgUserOauth2PermissionGrant; unfamiliar app consents, App ID = IOC"], icon="app-window", accent=C.purple, shadow=False, body_size=11)
d.card(zx + 16, 458, 258, 72, "Registered devices", ["new or unknown devices tied to the account"], icon="devices", accent=C.purple, shadow=False, body_size=11)
d.card(zx + 290, 458, 254, 72, "Sign-ins, 7 days", ["interactive and non-interactive; MFA previously satisfied elsewhere"], icon="doc-search", accent=C.purple, shadow=False, body_size=11)

d.zone(zx, 560, zw, 140, "Logs already kept for 90 days", icon="server-stack", note="Sentinel or Log Analytics, SOP-AZ-107")
d.card(zx + 16, 600, 258, 88, "Entra audit log", ["User registered security info, Update user, Consent to application"], icon="document", accent=C.teal, shadow=False, body_size=11)
d.card(zx + 290, 600, 254, 88, "Purview Unified Audit Log", ["MailItemsAccessed (licence and auditing on), UpdateInboxRules; Bind = opened, Sync = whole folder"], icon="doc-check-green", accent=C.teal, shadow=False, body_size=11)

# ---------------- arrows into the case folder
for yy in (207, 437, 630):
    d.arrow([(zx + zw, yy), (zx + zw + 36, yy), (zx + zw + 36, 388), (zx + zw + 60, 388)], C.grey, sw=1.6)

# ---------------- case folder (centre-right)
cx = 660
d.zone(cx, 300, 300, 180, "The case folder", icon="folder", fill=C.bluetint, stroke=C.blue, title_color=C.blue, note="C:\\IR\\INC-<id>")
d.card(cx + 14, 340, 272, 58, "Access-restricted folder", ["or a Purview eDiscovery case for Sev 1–2"], icon="lock", accent=C.blue, shadow=False, body_size=11)
d.card(cx + 14, 408, 272, 62, "One file per export", ["inboxrules.xml · forwarding.xml · authmethods.json · oauthgrants.json"], icon="document", accent=C.blue, shadow=False, body_size=10.5, mono_body=False)
d.arrow([(cx + 300, 388), (cx + 336, 388)], C.blue)

# ---------------- hash + ticket (right)
rx = 1000
d.card(rx, 300, 248, 84, "hashes.csv", ["Get-FileHash -Algorithm SHA256 over every file in the folder, exported once the set is complete"], icon="hash-doc", accent=C.green, shadow=False, body_size=11)
d.card(rx, 396, 248, 84, "Incident ticket", ["severity, incident manager, and every action logged with time and operator"], icon="ticket", accent=C.gold, shadow=False, body_size=11)

# ---------------- why first + what happens next
d.callout(660, 100, 588, 184, "Why this comes before step 1 of containment", kind="warn", icon="warning",
          body=["Removing a rule deletes its definition. Resetting MFA removes the attacker's method. Revoking the grant hides which app was consented. Once gone, nothing proves what the attacker set up or when.",
                "Export, then hash, then contain. The exports are also the baseline for eradication: after 24 quiet hours the same exports are re-run and diffed."])
d.zone(660, 500, 588, 186, "What the evidence answers later", icon="target", fill=C.greentint, stroke=C.green, title_color=C.green)
d.card(676, 540, 272, 62, "Scoping", ["timeline from the first suspicious sign-in; pivot on IPs, URL, recipients, consenting users"], accent=C.green, shadow=False, body_size=11)
d.card(960, 540, 272, 62, "Verify at the end", ["case folder: all exports present and listed in hashes.csv"], accent=C.green, shadow=False, body_size=11)
d.card(676, 612, 556, 62, "Legal and notification", ["notification deadlines can run in days or hours: give legal the facts early, from the exports, not from memory"], accent=C.green, shadow=False, body_size=11)

d.chips(32, 716, [("Exchange Online", C.blue), ("Entra ID", C.purple), ("logs", C.teal), ("case folder", C.blue), ("integrity", C.green)])
d.note_bottom("Exports named in Step 5; never email the user, the attacker may be reading the mailbox. Controls: IR-4, IR-5, AU-6, SI-4; 21 CFR Part 11 §11.10(e) audit trails retained for review.")
d.render(repo_path("security-operations/diagrams/sop-sec-002-3.svg"))
