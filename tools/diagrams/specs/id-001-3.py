import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("The eight policies: users, apps, conditions, grant and state",
            "What each baseline policy includes and excludes, what it targets, what it demands, and which enforcement wave switches it on. BG = the two break-glass accounts.",
            height=820)

d.zone(32, 100, 1216, 534, "The baseline, policy by policy", icon="policy-shield", note="every policy is created Report-only, then pilot, then On")

# column geometry
cols = [(48, 226, "Policy"), (284, 232, "Users: include → exclude"), (526, 330, "Target · conditions"), (866, 212, "Grant or session"), (1088, 144, "Enforce wave")]
hy = 158
d.rect(48, hy - 18, 1184, 26, fill=C.zone, stroke=C.border, rx=4)
for x, w, label in cols:
    d.text(x + 8, hy, label, 11.5, 600, C.ink)

rows = [
    ("CA001", "LegacyAuth-Block", "All users → BG", "All resources · client apps Exchange ActiveSync and Other clients", "Block", C.red, "1", ["legacy clients fail with 53003"]),
    ("CA002", "SecurityInfo-Register", "All users → BG, guests", "User action Register security information · any location except trusted", "Auth strength: MFA", C.blue, "1", ["TAP for untrusted networks (53004)"]),
    ("CA003", "AllApps-RequireMFA", "All users → BG, directory sync account", "All resources", "Auth strength: MFA", C.blue, "1", ["service accounts → workload identities"]),
    ("CA004", "Admins-PhishResistant", "14 privileged directory roles (BG caught via role, not excluded)", "All resources", "Phishing-resistant MFA", C.purple, "2", ["session: sign-in frequency 4 h", "FIDO2 key or passkey per admin first"]),
    ("CA005", "AzureMgmt-RequireMFA", "All users → BG", "Windows Azure Service Management API", "Auth strength: MFA", C.blue, "1", ["session: sign-in frequency every time", "portal, CLI and PowerShell management"]),
    ("CA006", "Sensitive-Compliant", "All users → BG, guests", "Exchange Online, SharePoint Online · Windows, macOS, iOS, Android", "Require compliant device", C.green, "2", ["needs Intune compliance reporting"]),
    ("CA007", "BlockedCountries-Block", "All users → BG, travel exception group (dated memberships)", "All resources · location Blocked countries", "Block", C.red, "2", ["Blocked countries named location"]),
    ("CA008", "Risk-Remediate", "All users → BG", "Sign-in risk High · separate policy for user risk High", "MFA · secure password change", C.gold, "P2", ["Report-only unless P2 is licensed"]),
]
y = 180
rh = 56
for pid, name, users, target, grant, col, wave, notes in rows:
    d.card(48, y, 1184, rh - 6, "", [], accent=col, shadow=False)
    d.text(66, y + 21, pid, 13.5, 600, col)
    d.text(66, y + 38, name, 11.5, 400, C.grey)
    d.lines(292, y + 19, users, 11.5, 216, 400, C.ink, lh=15)
    d.lines(534, y + 19, target, 11.5, 314, 400, C.ink, lh=15)
    d.pill(874, y + 7, grant, col)
    for i, n in enumerate(notes):
        d.text(874, y + 38 + i * 12, n, 10, 400, C.grey, max_w=206)
    if wave == "P2":
        d.pill(1096, y + 14, "Report-only · P2 decision", C.gold)
    else:
        d.badge(1110, y + 25, wave, C.blue if wave == "1" else C.purple)
        d.text(1128, y + 29, "same window" if wave == "1" else "after re-test", 11, 400, C.grey)
    y += rh

# bottom: how they combine
d.zone(32, 650, 596, 104, "How the eight combine at sign-in", icon="merge-purple")
d.card(48, 688, 184, 54, "Every match applies", ["no ordering, no first-match"], accent=C.purple, shadow=False, body_size=11)
d.card(240, 688, 184, 54, "All requirements met", ["MFA and device and strength"], accent=C.purple, shadow=False, body_size=11)
d.card(432, 688, 184, 54, "One block wins", ["CA001 or CA007 ends it"], accent=C.red, shadow=False, body_size=11)

d.zone(652, 650, 596, 104, "Two rules that keep the door open", icon="breakglass", fill=C.redtint, stroke=C.red, dashed=True, title_color=C.red)
d.card(668, 688, 278, 54, "Break-glass: only CA004 applies", ["FIDO2 keys always satisfy it; alert on sign-in"], accent=C.red, shadow=False, body_size=11)
d.card(958, 688, 274, 54, "Security defaults off with wave 1", ["same change window as wave 1, never alone"], accent=C.red, shadow=False, body_size=11)

d.note_bottom("Wave 1: CA001, CA002, CA003, CA005 switched On, then security defaults Disabled. Wave 2: CA004, CA006, CA007, re-testing after each. Controls: IA-2(1)(2), IA-2(6), AC-2, AC-7, AC-17.")
d.render(repo_path("identity-access/diagrams/sop-id-001-3.svg"))
