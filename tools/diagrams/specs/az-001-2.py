import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Decide before you click Create: what the tenant wizard makes permanent",
            "Three values cannot be changed afterwards and two choices cannot be converted later, so they are settled before the wizard opens, not inside it.",
            height=660)

# ---------------- permanent values
d.zone(32, 100, 600, 304, "Permanent once the tenant exists", icon="lock", note="no rename, no move, no second chance")
perm = [
    {"title": "Organisation name", "body": ["Set once in the wizard; there is no rename afterwards"], "icon": "id-card", "accent": C.red, "pill": ("permanent", C.red)},
    {"title": "Initial domain  <name>.onmicrosoft.com", "body": ["Permanent, and the two emergency access accounts live on it (step 2), so it deserves the same care as the custom domain"], "icon": "globe", "accent": C.red, "pill": ("permanent", C.red)},
    {"title": "Country or region", "body": ["Sets where the directory data lives; it cannot be changed after creation"], "icon": "hierarchy", "accent": C.red, "pill": ("permanent", C.red)},
]
d.card_col(48, 140, 568, 76, perm, gap=10)

# ---------------- one-way choices
d.zone(656, 100, 592, 304, "Choices that cannot be converted later", icon="question-diamond-gold", note="letters mark the alternatives")
d.text(672, 152, "Tenant type", 12.5, 600, C.ink)
d.card(672, 160, 276, 88, "Microsoft Entra ID", ["Standard workforce tenant: the one this runbook builds"], badge="A", badge_color=C.green, accent=C.green, pill=("choose", C.green))
d.card(960, 160, 272, 88, "Azure AD B2C", ["Customer identity tenant; a B2C tenant cannot be converted into Entra ID"], badge="B", badge_color=C.red, accent=C.red, pill=("one-way", C.red))
d.text(672, 284, "Cloud", 12.5, 600, C.ink)
d.card(672, 292, 276, 88, "Azure (global)", ["The default for everything that is not US government work"], badge="A", badge_color=C.blue, accent=C.blue, pill=("default", C.blue))
d.card(960, 292, 272, 88, "Azure Government", ["Build there instead for US government workloads; it is a separate cloud, not a setting"], badge="B", badge_color=C.gold, accent=C.gold, pill=("US gov", C.gold))

# ---------------- before opening the wizard
d.zone(32, 424, 1216, 148, "Have these ready before the wizard opens", icon="checklist-purple")
ready = [
    {"title": "Private browser window", "body": ["If you are signed in to another tenant, so the new tenant is created under the right account"], "icon": "app-window", "accent": C.purple, "badge": "1"},
    {"title": "A place for the tenant ID", "body": ["Every later step and every evidence item points back to it"], "icon": "document", "accent": C.purple, "badge": "2"},
    {"title": "Emergency account owners", "body": ["Cloud-only, not tied to one person, FIDO2 keys or long random passwords stored offline"], "icon": "breakglass", "accent": C.purple, "badge": "3"},
    {"title": "Registrar access (MS= TXT)", "body": ["Custom domain verification (step 4) waits on DNS propagation"], "icon": "globe", "accent": C.purple, "badge": "4"},
]
d.card_row(48, 464, 290, 94, ready, gap=12)

d.note_bottom("Three permanent values, two one-way choices, four things to have ready. Controls supported: CM-2, PL-8 (governance in place before workloads); GV.PO-01.")
d.render(repo_path("azure-procedures/diagrams/sop-az-001-2.svg"))
