import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Boot integrity, encryption layers and the residency guardrail",
            "How Trusted Launch starts the VM, what each encryption layer covers, and how Azure Policy refuses a resource outside the approved region.",
            height=756)

# ---------------- boot chain (left)
d.zone(32, 100, 384, 420, "Boot integrity: Trusted Launch", icon="shield-check", note="Basics tab")
chain = [
    ("Gen2 image, supported size", ["Windows Server 2025 Azure Edition Gen2; a Gen1 image or unsupported family greys the option out"], "windows", C.grey),
    ("Secure Boot", ["UEFI accepts only signed boot components, which is what stops bootkits"], "lock", C.blue),
    ("vTPM", ["A virtual TPM holds the boot measurements; Get-Tpm shows it inside the guest"], "chip", C.blue),
    ("Integrity monitoring", ["Boot measurements reported to Defender for Cloud, so a tampered boot shows as a finding"], "doc-check-green", C.green),
]
yy = 140
for i, (title, body, ic, col) in enumerate(chain):
    d.card(48, yy, 352, 78, title, body, icon=ic, accent=col, badge=str(i + 1), badge_color=col, body_size=11.5)
    if i < 3:
        d.arrow([(224, yy + 78), (224, yy + 88)], col, sw=1.6)
    yy += 88
d.text(48, 500, "Guest: Confirm-SecureBootUEFI is True; Get-Tpm shows a TPM.", 11, 400, C.grey, max_w=352)

# ---------------- encryption layers (middle)
d.zone(440, 100, 384, 420, "What each encryption layer covers", icon="key", note="Disks tab")
layers = [
    ("Server-side encryption (SSE)", ["AES-256 on every managed disk, always on, platform-managed keys"], "ssd", C.blue, "always on"),
    ("Encryption at host", ["Adds the temp disk and the OS and data disk caches; the EncryptionAtHost feature is registered once per subscription"], "server", C.purple, "tick it"),
    ("Customer-managed key", ["Optional: a disk encryption set pointing at your Key Vault key, for disks that must use your key"], "lock", C.gold, "optional"),
]
yy = 140
for i, (title, body, ic, col, pill) in enumerate(layers):
    d.card(456, yy, 352, 92, title, body, icon=ic, accent=col, body_size=11.5, pill=(pill, col))
    if i < 2:
        d.arrow([(632, yy + 92), (632, yy + 102)], col, sw=1.6)
    yy += 102
d.callout(456, 446, 352, 66, "ADE (BitLocker in the guest) is retiring", kind="warn", body=["Use encryption at host instead for new builds."])

# ---------------- residency guardrail (right)
d.zone(848, 100, 400, 420, "Residency guardrail at work", icon="policy-shield", note="platform team assigns it")
d.card(864, 140, 368, 62, "Request: create VM in another region", ["any client: portal, PowerShell, CLI or Bicep"], icon="arrows-lr", accent=C.grey, body_size=11.5)
d.arrow([(1048, 202), (1048, 216)], C.grey, sw=1.6)
d.card(864, 218, 368, 80, "Allowed locations · Deny", ["Built-in definition e56962a6-4747-49cd-b67b-bf8b01975c4c, evaluated before the resource exists"], icon="x-circle", accent=C.red, body_size=11.5, pill=("Deny", C.red))
d.arrow([(1048, 298), (1048, 310)], C.red, sw=1.6)
d.card(864, 312, 368, 74, "RequestDisallowedByPolicy", ["The error names the assignment; correct the region or tag value rather than asking for an exemption"], icon="warning", accent=C.red, body_size=11.5)
d.arrow([(1048, 386), (1048, 398)], C.grey, sw=1.6)
d.card(864, 400, 368, 108, "Everything that supports the VM", ["Backups, Log Analytics, diagnostic storage and DR replicas must stay in the region too; a region keeps data in-country but does not change which laws can compel the provider"], icon="hierarchy", accent=C.green, body_size=11.5, pill=("in-region", C.green))

# ---------------- other guardrails strip
d.zone(32, 540, 1216, 134, "The four policy assignments from step 11", icon="checklist-purple", note="effect decides whether the build is stopped or only scored")
pols = [
    {"title": "Allowed locations", "body": ["Deny: wrong region never exists"], "icon": "globe", "accent": C.red, "pill": ("Deny", C.red)},
    {"title": "Require a tag", "body": ["Deny, one assignment per mandatory tag"], "icon": "ticket", "accent": C.red, "pill": ("Deny", C.red)},
    {"title": "Encryption at host", "body": ["Audit or Deny: a VM without it is scored, or stopped"], "icon": "server", "accent": C.gold, "pill": ("Audit or Deny", C.gold)},
    {"title": "Management ports closed", "body": ["Audit: open RDP or SSH shows in compliance"], "icon": "ports-blue", "accent": C.gold, "pill": ("Audit", C.gold)},
]
d.card_row(48, 580, 290, 80, pols, gap=12, body_size=11.5)

d.note_bottom("Worked example: Germany West Central, one VM per zone; a Trusted Launch VM needs an Enhanced backup policy. Controls: SC-28 (encryption), CM-6 and Allowed locations (residency); tags record scope.")
d.render(repo_path("azure-procedures/diagrams/sop-az-002-3.svg"))
