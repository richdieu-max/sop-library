import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Secrets at service start: how the VM reads the vault without holding a key",
            "The service proves who it is to IMDS, receives a short-lived token, and reads only the secrets its role allows; nothing lands on disk, in the image or in source control.",
            height=720)

# ---- sequence (left 850px)
actors = [("App service (systemd)", "gear-box", C.purple), ("IMDS 169.254.169.254", "server", C.grey),
          ("Microsoft Entra ID", "entra-user", C.blue), ("Key Vault (private endpoint)", "lock", C.gold)]
msgs = [
    (0, 1, "GET /metadata/identity/oauth2/token  (Metadata: true)", C.purple, False),
    (1, 2, "asks for a token for resource vault.azure.net", C.grey, False),
    (2, 1, "access token for the VM's system-assigned identity", C.blue, True),
    (1, 0, "token, valid about an hour, never written anywhere", C.grey, True),
    (0, 3, "GET /secrets/app-jwt-secret  Authorization: Bearer <token>", C.purple, False),
    (3, 3, "RBAC: is this identity a Secrets User here?", C.gold, False),
    (3, 3, "AuditEvent: who, which secret, result", C.gold, False),
    (3, 0, "secret value, over the private endpoint only", C.gold, True),
    (0, 0, "write /run/app/env on tmpfs, umask 077", C.purple, False),
]
bottom = d.sequence(32, 100, 840, actors, msgs, lane_h=38)

# ---- right column: what never happens, and the three identities
d.zone(900, 100, 348, 282, "What never happens", icon="shield-x", fill=C.redtint, stroke=C.red, dashed=True, title_color=C.red)
cards = [
    {"title": "No key on the VM", "body": ["The identity is the credential;", "Azure injects it, nobody copies it"], "icon": "key", "accent": C.red},
    {"title": "No secret on disk or in the image", "body": ["tmpfs only, readable by the service", "user, cleared at reboot"], "icon": "ssd", "accent": C.red},
    {"title": "No secret in source control", "body": ["fetch-secrets.template.sh holds", "names, never values"], "icon": "git-branch", "accent": C.red},
]
d.card_col(916, 140, 316, 66, cards, gap=12)

d.zone(900, 398, 348, 246, "Three identities, three different rights", icon="users")
d.card(916, 438, 316, 54, "VM system-assigned identity", ["Key Vault Secrets User: read values only"], icon="vm-cluster", accent=C.purple,
       pill=("read", C.green))
d.card(916, 500, 316, 62, "Disk encryption set identity", ["Crypto Service Encryption User: wrap and unwrap"], icon="hash-doc", accent=C.gold,
       pill=("keys", C.gold))
d.card(916, 570, 316, 62, "Operator (temporary)", ["Secrets Officer during seeding; removed by the hardening pass"], icon="user", accent=C.grey,
       pill=("removed", C.red))

# ---- bottom strip: why the private endpoint matters
d.zone(32, bottom + 16, 840, 94, "Why the private endpoint matters", icon="link", note="public network access: Disabled")
d.lines(46, bottom + 58, "The vault answers only on a private IP inside snet-pe, resolved through the linked private DNS zone. A stolen token used from anywhere outside the spoke is refused before RBAC is even consulted, and the outside-in test in SOP-AZ-105 proves that refusal every run.", 12, 812)

d.note_bottom("Controls supported: IA-5 (no stored secrets), SC-12 and SC-28 (keys and encryption), AU-2 (vault AuditEvent). Token lifetime and tmpfs path are the template defaults.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-102-2.svg"))
