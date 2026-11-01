import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Four layers of protection on one VM: boot, host, disk, backup",
            "Each layer answers a different failure: malware before the OS loads, data left in caches, a disk copied out of the tenant, and a copy held only at the same site.",
            height=740)

# ---- left: the stack (bottom = boot, top = backup) drawn top-down as layers
layers = [
    ("4", "Backup", "Recovery Services vault", ["Geo-redundant, cross-region restore on, immutable (unlocked), public network access off. Set GRS and cross-region restore before the first item is protected: redundancy locks after that"], "refresh-green", C.green, "copies never only at the same site"),
    ("3", "Disks", "Disk encryption set", ["Customer-managed RSA 3072 HSM key from the vault, double encryption with platform and customer keys, auto key rotation on; data disk on the same set"], "ssd", C.gold, "the client can revoke the key and every disk becomes unreadable"),
    ("2", "Host", "Encryption at host", ["Temp disk and caches encrypted too, so nothing readable is left on the physical host. Needs the EncryptionAtHost feature registered on the subscription"], "server", C.purple, "no clear-text spill outside the disks"),
    ("1", "Boot", "Trusted Launch", ["Secure Boot and vTPM on the VM; patch orchestration Azure orchestrated; system-assigned managed identity"], "shield-check", C.blue, "blocks boot-level malware"),
]
y = 108
for n, short, title, body, icon, col, why in layers:
    d.card(32, y, 560, 112, f"{short} · {title}", body, icon=icon, accent=col, badge=n, badge_color=col)
    d.text(96, y + 100, why, 11, 600, col, max_w=470)
    y += 122

# ---- right: the vault that holds the key, and the identities
d.zone(628, 100, 620, 300, "The vault behind the disk key", icon="lock", note="Premium · RBAC · private endpoint only")
d.card(644, 140, 282, 110, "Key Vault", ["Premium tier, soft delete 90 days, purge protection on, RBAC authorization, public access disabled, private endpoint in snet-pe with private DNS"], icon="lock", accent=C.gold, shadow=False, body_size=11)
d.card(944, 140, 288, 110, "RSA 3072 HSM key", ["Created in the vault with an expiry date. Stays in the vault; the disk encryption set wraps the disk keys with it and rotates automatically"], icon="key", accent=C.gold, shadow=False, body_size=11)
d.card(644, 264, 282, 110, "Disk set identity", ["Granted Key Vault Crypto Service Encryption User on the vault when the set is created: wrap and unwrap only"], icon="hash-doc", accent=C.gold, shadow=False, body_size=11, pill=("keys", C.gold))
d.card(944, 264, 288, 110, "VM identity", ["Key Vault Secrets User only: reads secret values at service start and holds no key role at all (see the secrets figure)"], icon="vm-cluster", accent=C.purple, shadow=False, body_size=11, pill=("read", C.green))
d.arrow([(592, 300), (644, 300)], C.gold, sw=1.5)

# ---- right-bottom: repeatability
d.callout(628, 424, 620, 122, "The next customer changes two values", kind="info", icon="code-braces",
          body=["Same template, same four layers. To onboard c002 change customerCode and the spoke address space (for example 10.2.0.0/16) in the parameter file and run SOP-02-customer-stamp.ps1 with -WhatIf first.",
                "A hardening pass at the end closes any bootstrap window and removes the operator's temporary vault role, even if a step failed part way."])
d.callout(628, 562, 620, 98, "Rollback keeps the key", kind="warn", icon="key",
          body=["Stop backup with retain data, then remove the stamp resource group. Purge protection keeps the vault recoverable for 90 days, and the disk key must stay until every recovery point that used it has expired."])

d.note_bottom("Controls: SC-12, SC-28 (customer-managed key, encryption at rest and at host), CP-9, CP-10 (geo-redundant, immutable backup with cross-region restore), CIS Azure Foundations 7.x. Numbers are the template defaults.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-102-3.svg"))
