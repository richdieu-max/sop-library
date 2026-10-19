# SOP-AZ-102 · Deploying a repeatable customer stamp

Deploy one identical, isolated unit per customer from one template: its own resource group, private spoke network, VM, Key Vault read by the VM managed identity, customer-managed disk keys and geo-redundant backup to the paired region. Because every stamp comes from the same template, the tenth customer is as well built as the first, and a reviewer who has checked one stamp knows what every other looks like.

**Family:** Azure landing zone series · **Covers:** the stamp in the portal and from the template, on top of the SOP-AZ-101 foundation · **Does not cover:** the foundation itself (SOP-AZ-101), PIM for the customer operations group (SOP-AZ-104), or the outside-in vault test (SOP-AZ-105).

## How it fits together

![The spoke VNet peers with the hub; the app VM has no public IP, gets a token from IMDS, calls Key Vault over a private endpoint and may only read secret values; disks use a customer-managed key through a disk encryption set and backups go geo-redundant to the paired region](diagrams/sop-az-102-1.svg)

Secrets live in the vault the way valuables live in a safe-deposit box. The VM does not carry the key; it proves who it is at the counter (IMDS), receives a short-lived ticket and reads only the box it is allowed to read.

| Layer | Control | Why |
|---|---|---|
| Disks | Disk encryption set with a customer-managed RSA 3072 HSM key, double encryption, auto rotation | The client can revoke the key and every disk becomes unreadable |
| Host | Encryption at host | Temp disk and caches are encrypted too |
| Boot | Trusted Launch with Secure Boot and vTPM | Blocks boot-level malware |
| Backup | Recovery Services vault, geo-redundant, cross-region restore, immutable (unlocked) | Copies are never held only at the same site as the tenant |

## Before you start

| Item | Requirement |
|---|---|
| Create the stamp | Contributor on the customer subscription; the SOP-AZ-101 foundation must exist |
| Grant vault roles | User Access Administrator (or Owner) on the stamp resource group only |
| Seed secrets | Key Vault Secrets Officer, temporary, removed by the hardening pass at the end of the run |
| After hand-over | Customer operations group, eligible Contributor on Customers through PIM |
| Capacity | Quota for the VM family in the region, and the size not capacity-restricted for the subscription. Newer v6 sizes need the NVMe disk controller |
| Subscription | `EncryptionAtHost` feature registered |
| Addressing | Customer code chosen (for example `c001`); spoke address space does not overlap the hub or other stamps |
| App | Application port and the gateway subnet that may reach it agreed with the app team |
| Egress | NAT gateway for a fixed outbound IP; plan Azure Firewall instead if the design needs an FQDN allow-list |
| Later secret writes | A person with Secrets Officer, through an in-network path or a short selected-networks window. The VM stays read-only |
| Backup redundancy | Locks once any item is protected: set Geo-redundant and cross-region restore before enabling VM backup |

## Steps

### Portal

1. **Spoke network and NSG.** Create the stamp resource group with the three required tags. Create a **Network security group**: SSH 22 from the hub management subnet only, the app port from the gateway subnet only, deny Internet inbound at 4000, HTTPS 443 out to AzureCloud, deny all outbound at 4000. Create the spoke VNet with `snet-app` (NSG attached) and `snet-pe`, then add **Peerings** both ways with the hub.
2. **Key Vault.** **Key vaults › Create**: Premium, soft delete 90 days, **Purge protection: Enable**. **Access configuration:** Azure role-based access control. **Networking:** Disable public access, and add a private endpoint in `snet-pe` with private DNS integration.
3. **Key and disk encryption set.** In the vault create an RSA 3072 HSM key with an expiry date. **Disk Encryption Sets › Create**: **Double encryption with platform-managed and customer-managed keys**, select the vault and key, turn on **Auto key rotation**. Grant the set's identity **Key Vault Crypto Service Encryption User** on the vault when prompted.
4. **VM.** **Virtual machines › Create**, security type **Trusted launch** with Secure Boot and vTPM. Disks: encryption at host on, key management **Customer-managed key** with the set, data disk on the same set. Networking: `snet-app`, **Public IP: None**, NIC NSG None (the subnet NSG applies). Management: **Enable system assigned managed identity**; patch orchestration Azure orchestrated.
5. **Read-only access to secrets.** Vault › **Access control (IAM) › Add › Add role assignment**: **Key Vault Secrets User**, assign to **Managed identity**, select the VM. Give the VM no other vault role. Evidence lists secret names, enabled state and expiry only; never export or screenshot a value.
6. **Geo-redundant backup.** Create a Recovery Services vault. Before protecting anything, **Properties › Backup Configuration › Update**: **Geo-redundant**, **Cross Region Restore: Enabled**, **Apply**. Turn on **Immutable vault** (unlocked) and disable public network access. Pre-create the tagged `AzureBackupRG_<region>_1` resource group so the tag policy does not refuse it, then enable backup for the VM with a daily policy.

### Template

7. **Run `SOP-02-customer-stamp.ps1`.** It builds the stamp in the order above, then a hardening pass closes any bootstrap window and removes the operator's temporary vault role, even if a step fails part way. One parameter, `customerCode`, separates one customer from the next. To onboard the next customer, change `customerCode` and the spoke address space only:

   ```powershell
   (Get-Content tenant.parameters.json | ConvertFrom-Json) | ForEach-Object { $_.customerCode = 'c002';
     $_.stamp.addressSpace = '10.2.0.0/16'; $_ } |
     ConvertTo-Json -Depth 10 | Set-Content tenant.c002.parameters.json
   ./SOP-02-customer-stamp.ps1 -ParameterFile ./tenant.c002.parameters.json -WhatIf
   ```

8. **Fetch secrets on the VM.** At service start, `fetch-secrets.template.sh` gets a token from IMDS for the managed identity, reads each secret over the private endpoint, and writes them to a tmpfs file readable only by the service user, gone at reboot. No secret is stored on disk, in the image or in source control.

   ```bash
   TOKEN=$(curl -s -H "Metadata: true" \
     "http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https%3A%2F%2Fvault.azure.net" \
     | python3 -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')
   get() { curl -s -H "Authorization: Bearer $TOKEN" "https://$VAULT.vault.azure.net/secrets/$1?$API" \
           | python3 -c 'import sys,json; print(json.load(sys.stdin)["value"])'; }
   umask 077
   { echo "JWT_SECRET=$(get app-jwt-secret)"; } > /run/app/env   # tmpfs, service user only
   ```

## Verify

The exit criterion: no public IP on the VM, the vault read by the VM identity only, and GRS backup with cross-region restore.

| Check | Pass |
|---|---|
| Vault roles | `Get-AzRoleAssignment -Scope <vault id>` lists only the VM identity (Secrets User) and the disk set (Crypto Service Encryption User) |
| Exposure | `Get-AzNetworkInterface` shows no public IP configuration on the VM NIC |
| Backup | `Get-AzRecoveryServicesBackupProperty` reads GeoRedundant and cross-region restore True |
| First backup | One on-demand backup completed; job ID and time recorded |
| Outside-in | Listing vault secrets from outside the network is refused (SOP-AZ-105) |

## Rollback

Stop backup protection with retain data, then remove the stamp resource group. Purge protection keeps the vault recoverable for 90 days, and the disk encryption key must stay until every recovery point that used it has expired.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| VM create fails on size | Zero quota or a capacity restriction for that family; request quota or choose another size |
| VM create fails on disk controller | v6 sizes are NVMe-only; set the disk controller type to NVMe |
| Service cannot read secrets | Missing Secrets User role, role not yet propagated, or private DNS zone not linked to the spoke |
| First backup fails with a policy error | Azure Backup tried to create an untagged `AzureBackupRG_*` group; pre-create it with the required tags |
| Cannot set GRS on the vault | An item is already protected; stop protection (retain data), change redundancy, protect again |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| CIS Azure Foundations | 7.x, 8.x | VM and Key Vault baselines in every stamp |
| NIST SP 800-53 R5 | SC-7 | Spoke peers only with the hub; no public IP; default-deny NSG |
| | SC-12, SC-28 | Customer-managed HSM key with rotation; encryption at rest and at host |
| | IA-5 | No stored secrets: managed identity and short-lived IMDS tokens |
| | CP-9, CP-10 | Geo-redundant, immutable backup with cross-region restore |
| ISO/IEC 27001:2022 | A.8.13, A.8.20, A.8.24 | Backup, network security, cryptography |
| HIPAA Security Rule | 164.308(a)(7), 164.312(a)(2)(iv) | Contingency plan; encryption and decryption |
