# SOP-AZ-105 · Scanning for secrets and supply-chain risk

Run gitleaks, Trivy and Dependabot across the full history of the repository the client names as canonical, build a licence inventory, and confirm the secrets live in a private Key Vault the workload can only read. A secret committed once stays in the history even after the line is deleted, so scanning only the current files misses it.

**Family:** Azure landing zone series · **Covers:** secrets scanning of every commit, CVE and misconfiguration scanning, SBOM and licence inventory, Dependabot export, a read-only Key Vault posture check and a hashed evidence bundle · **Does not cover:** code review.

## Flow

Cleaning the living room (the current branch) does not empty the attic (every old commit). gitleaks searches the attic, Trivy checks what was built from it, and Dependabot watches what new boxes arrive.

![Written authorization comes first, then a mirror clone of the canonical repository, then gitleaks, Trivy and Dependabot scans, a hashed manifest and a report; below, the Key Vault check confirms public access is disabled and listing secrets from outside is refused](diagrams/sop-az-105-1.svg)

| Tool | Finds | Output |
|---|---|---|
| gitleaks | Keys, tokens, passwords and connection strings in every commit | JSON with file, commit and rule (values redacted) |
| Trivy | CVEs, secrets and misconfiguration in files, IaC and images; SBOM | JSON, CycloneDX |
| Dependabot | Known-vulnerable dependencies, continuously | Open alerts from GitHub |

## Before you start

| Item | Requirement |
|---|---|
| Authorization | Written authorization on file that names the repository the client treats as canonical, and the dates. Do not scan until you hold it. Never scan a fork or a developer copy |
| Repository | Read on the canonical repository, all branches; canonical repository confirmed by its owner |
| Dependabot export | Security events read, with a token scoped to the one repository |
| Vault check | Reader on the vault resource group; data-plane read is not needed |
| Tools | gitleaks 8.x and Trivy 0.5x installed on the scanning machine |
| Evidence | Evidence folder created with a run ID |

## Steps

1. **Clone and scan history for secrets.** Clone fresh with all branches: `git clone --mirror <repo-url>`. Run `gitleaks git <repo> --log-opts="--all" --redact`. Triage every hit as a real secret (rotate it in the vault, then purge history), a test value or a false positive. Record file, commit and rule only. A report that contains the secret has just leaked it again: reference the commit and rule, and rotate the secret before the report is sent.
2. **Scan for CVEs, misconfiguration and licences.** Run Trivy over the filesystem with `--scanners vuln,secret,misconfig --severity CRITICAL,HIGH`. Scan the deployed image too, if there is one. Generate a CycloneDX SBOM for the licence inventory and export open Dependabot alerts.

   ```bash
   set -euo pipefail
   REPO="${1:?path to repo clone}"; OUT="${2:-./scan-$(date -u +%Y%m%dT%H%M%SZ)}"; mkdir -p "$OUT"
   gitleaks git "$REPO" --log-opts="--all" --redact --report-format json --report-path "$OUT/gitleaks.json" || true
   trivy fs "$REPO" --scanners vuln,secret,misconfig --severity CRITICAL,HIGH --format json -o "$OUT/trivy-fs.json"
   # trivy image <registry>/<image>:<tag> --severity CRITICAL,HIGH --format json -o "$OUT/trivy-image.json"
   trivy fs "$REPO" --format cyclonedx -o "$OUT/sbom.cdx.json"
   # gh api "repos/<owner>/<repo>/dependabot/alerts?state=open&per_page=100" > "$OUT/dependabot-open.json"
   ( cd "$OUT" && sha256sum * > MANIFEST.sha256 )
   ```

3. **Check the vault is private.** Open the vault › **Settings › Networking**: **Disable public access** should be selected; trusted Microsoft services may bypass for platform features only. Open **Private endpoint connections**: the stamp's endpoint should be **Approved**. `SOP-05-keyvault-check.ps1` reads the same posture and lists role assignments and secret names only, never values.

   ```powershell
   $kv = Get-AzKeyVault -VaultName $VaultName -ResourceGroupName $ResourceGroup
   [pscustomobject]@{
     RbacMode        = $kv.EnableRbacAuthorization             # expect True
     PurgeProtection = $kv.EnablePurgeProtection               # expect True
     PublicNetwork   = $kv.PublicNetworkAccess                 # expect Disabled
     IpRules         = @($kv.NetworkAcls.IpAddressRanges).Count  # expect 0
   }
   Get-AzRoleAssignment -Scope $kv.ResourceId | Select-Object DisplayName, ObjectType, RoleDefinitionName
   ```

4. **Prove it from outside.** From a machine outside the private network open the vault › **Objects › Secrets**. The portal should refuse to list secrets. That refusal is the evidence that a stolen portal session alone cannot read them.
5. **Hash and report.** Hash every output into `MANIFEST.sha256` before anyone reads the results. Report counts by severity, the triage result for each secret hit, and the fix path for each CVE (owner role and target date).

## Verify

| Check | Pass |
|---|---|
| Evidence integrity | Manifest hashes match the delivered files |
| Secrets | Every gitleaks hit has a triage result; every real secret has a rotation record |
| Vulnerabilities | No CRITICAL rows in Trivy, or each has an accepted risk ID |
| Vault | Check prints RBAC True, purge protection True, public access Disabled, IP rules 0 |

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| gitleaks finds nothing in an old repo | Shallow clone. Re-clone with full history (`--mirror`) |
| Trivy DB download fails | Egress blocked. Use an offline DB bundle or run from an allowed network |
| Vault check shows an IP rule left behind | A bootstrap window was not closed. Remove the rule and record it as a finding |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | IA-5(7) No embedded unencrypted static authenticators | Full-history secrets scan; real secrets rotated and moved to the vault |
| | RA-5 Vulnerability monitoring and scanning | Trivy CVE and misconfiguration scans; Dependabot alerts |
| | SA-15, SR-3 | Development process and supply-chain risk: SBOM and dependency inventory |
| | SC-12 Cryptographic key management | Secrets held in a private vault with RBAC and purge protection |
| ISO/IEC 27001:2022 | A.8.8, A.8.24, A.8.28 | Technical vulnerabilities; use of cryptography; secure coding inputs |
| PCI DSS v4 (boundary) | 6.3, 8.6 | Vulnerabilities identified; application and system account secrets protected |
| ALCOA+ | Attributable, original, accurate | Outputs hashed into a manifest before anyone reads them |
