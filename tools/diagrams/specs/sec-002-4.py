import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Blast radius: what a taken-over account can reach, and which table proves it",
            "Scoping walks outward from the account: what the attacker read and sent, what they planted to survive a password reset, and who else they reached; each ring names its evidence.",
            height=700)

# ---------------- rings left and right
lx, rx, zw = 32, 848, 400
d.zone(lx, 100, zw, 300, "What they read and sent", icon="doc-search", fill=C.bluetint, stroke=C.blue, title_color=C.blue, note="MailItemsAccessed · trace")
d.card(lx + 16, 140, zw - 32, 58, "Mail opened", ["MailItemsAccessed Bind = messages opened"], icon="document", accent=C.blue, shadow=False, body_size=11, pill=("Bind", C.blue))
d.card(lx + 16, 206, zw - 32, 58, "Whole folders synced", ["Sync = treat the entire folder as accessed"], icon="folder", accent=C.blue, shadow=False, body_size=11, pill=("Sync", C.red))
d.card(lx + 16, 272, zw - 32, 58, "Mail sent from the account", ["message trace: internal phishing, payment-change requests"], icon="chat-dots", accent=C.blue, shadow=False, body_size=11)
d.card(lx + 16, 338, zw - 32, 54, "Files and other apps touched", ["CloudAppEvents; AuditLogs and OfficeActivity for changes"], icon="app-window", accent=C.blue, shadow=False, body_size=11)

d.zone(rx, 100, zw, 300, "What they planted to survive a reset", icon="lightning", fill=C.goldtint, stroke=C.gold, title_color=C.gold, note="steps 4–8")
d.card(rx + 16, 140, zw - 32, 58, "Inbox rules and Sweep", ["hidden rules that delete or move replies (UpdateInboxRules)"], icon="list-blue", accent=C.gold, shadow=False, body_size=11)
d.card(rx + 16, 206, zw - 32, 58, "Forwarding and delegates", ["SMTP forwarding; FullAccess, SendAs, SendOnBehalf, calendar"], icon="arrows-lr", accent=C.gold, shadow=False, body_size=11)
d.card(rx + 16, 272, zw - 32, 58, "OAuth app consent", ["an app with its own tokens keeps access after the reset"], icon="app-monitor", accent=C.gold, shadow=False, body_size=11)
d.card(rx + 16, 338, zw - 32, 54, "New MFA method or device", ["User registered security info; a device of their own"], icon="phone-x", accent=C.gold, shadow=False, body_size=11)

# ---------------- hub
hx, hy, hw, hh = 464, 120, 352, 280
d.zone(hx, hy, hw, hh, "Compromised account", icon="user", fill=C.redtint, stroke=C.red, title_color=C.red)
d.card(hx + 14, hy + 42, hw - 28, 60, "How they got in", ["EmailEvents and SigninLogs: lure, click, adversary-in-the-middle relay"], accent=C.red, shadow=False, body_size=11)
d.card(hx + 14, hy + 110, hw - 28, 60, "Stolen session cookie and tokens", ["the kit keeps them, so a reset alone does not end access"], accent=C.red, shadow=False, body_size=11)
d.card(hx + 14, hy + 178, hw - 28, 84, "Why revoke sits beside reset", ["CAE: Exchange, SharePoint and Teams reject tokens within minutes; other apps honour them until expiry, about 60–90 min"], icon="clock", accent=C.grey, shadow=False, body_size=11)

# ---------------- ring 3 (bottom): spread
d.zone(32, 440, 1216, 154, "Who else they reached: every hit restarts triage and containment", icon="users", fill=C.purpletint, stroke=C.purple, title_color=C.purple, note="stop when a pass finds nothing new")
d.card(48, 480, 286, 96, "Same attacker IPs", ["union SigninLogs and non-interactive sign-ins over 14 days: other accounts from the same IPs"], icon="globe", accent=C.purple, shadow=False, body_size=11)
d.card(350, 480, 286, 96, "Same phishing URL", ["UrlClickEvents: who else clicked the lure"], icon="link", accent=C.purple, shadow=False, body_size=11)
d.card(652, 480, 286, 96, "Recipients of the sent mail", ["the internal phishing wave; IT contacts them, not the user"], icon="chat-purple", accent=C.purple, shadow=False, body_size=11)
d.card(954, 480, 278, 96, "Same OAuth app", ["other users who consented to the malicious application"], icon="group-window", accent=C.purple, shadow=False, body_size=11)

# ---------------- connectors
d.arrow([(hx, 250), (lx + zw + 4, 250)], C.blue, sw=1.8)
d.arrow([(hx + hw, 250), (rx - 4, 250)], C.gold, sw=1.8)
d.arrow([(hx + hw / 2, hy + hh), (hx + hw / 2, 436)], C.purple, sw=1.8)

d.chips(32, 610, [("read / sent", C.blue), ("persistence", C.gold), ("spread", C.purple), ("entry", C.red)])
d.note_bottom("Tables from Steps 9–10: EmailEvents, SigninLogs, AADNonInteractiveUserSignInLogs, AuditLogs, OfficeActivity, MailItemsAccessed, CloudAppEvents, UrlClickEvents. Controls: IR-4, AU-6, SI-4; CSF RS.AN.")
d.render(repo_path("security-operations/diagrams/sop-sec-002-4.svg"))
