# aws-posture-check

A read-only security posture check for one AWS account. It verifies the baseline in [SOP-AWS-001](../../aws-procedures/SOP-AWS-001-creating-securing-aws-account.md) (root user, identity, logging, threat detection, storage defaults) and the hardened EC2 build in [SOP-AWS-002](../../aws-procedures/SOP-AWS-002-hardened-ec2-data-residency-region.md), plus the AWS Backup controls in [SOP-AWS-004](../../aws-procedures/SOP-AWS-004-multi-region-backup-disaster-recovery.md). Each run writes a hashed evidence folder that can go straight onto a change record.

**Safe to run: makes zero changes.** The tool only calls Describe, Get and List APIs, plus `iam:GenerateCredentialReport`, which asks IAM to build the account's credential report and changes no configuration. Every client is wrapped in a guard that refuses any other operation before it reaches AWS, and a unit test scans the check code for mutating calls.

## What it checks

Each check returns **PASS**, **WARN**, **FAIL** or **ERROR** for each resource, with the resource ID, region, detail, a remediation hint, the NIST SP 800-53 Rev 5 controls it supports and, where one exists, the CIS AWS Foundations Benchmark v3.0.0 recommendation. ERROR means the check could not be completed (access denied, service not available in the region, or an API failure); the run carries on.

Global checks run once against the home region and are reported as region `global` (CloudTrail rows show the trail's home region). Regional checks run in every region given to `--regions`.

| Check | Area | Scope | What it verifies | NIST 800-53 R5 | CIS v3.0.0 |
|---|---|---|---|---|---|
| IAM-01 | Identity | Global | Root user has MFA enabled | IA-2(1), AC-6(5) | 1.5 |
| IAM-02 | Identity | Global | Root user MFA is a security key or hardware device, not a virtual (app) device (WARN) | IA-2(1), IA-5 | 1.6 |
| IAM-03 | Identity | Global | Root user has no access keys | AC-6(5), IA-5 | 1.4 |
| IAM-04 | Identity | Global | Root user not used (password or keys) in the last 30 days (WARN) | AC-6(5), AC-2 | 1.7 |
| IAM-05 | Identity | Global | Account password policy: minimum length 14, reuse prevention 24. FAIL if missing and IAM console users exist, WARN if missing and none exist | IA-5(1) | 1.8, 1.9 |
| IAM-06 | Identity | Global | An IAM Identity Center instance exists in the home region (WARN if not) | AC-2, IA-2 | 1.21 |
| IAM-07 | Identity | Global | Every IAM user with a console password has MFA | IA-2(1), IA-2(2) | 1.10 |
| IAM-08 | Identity | Global | Active IAM user access keys: FAIL if older than 90 days, WARN if unused for 45 days | IA-5(1), AC-2(3) | 1.12, 1.14 |
| LOG-01 | Logging | Global | A multi-region CloudTrail trail exists, is logging, and records read and write management events | AU-2, AU-12 | 3.1 |
| LOG-02 | Logging | Global | Log file validation is on for each multi-region trail | AU-9, SI-7 | 3.2 |
| LOG-03 | Logging | Global | Multi-region trails encrypt logs with SSE-KMS (WARN if not; optional in SOP-AWS-001) | AU-9, SC-28 | 3.5 |
| LOG-04 | Logging | Regional | An AWS Config recorder is recording all supported resource types | CM-8, CA-7 | 3.3 |
| THR-01 | Threat protection | Regional | A GuardDuty detector exists and is enabled | SI-4, RA-5 | |
| THR-02 | Threat protection | Regional | Security Hub is enabled with at least one standard | CA-7, SI-4, RA-5 | 4.16 |
| THR-03 | Threat protection | Regional | An IAM Access Analyzer external access analyzer (account or organization) is active | AC-6, CA-7 | 1.20 |
| STO-01 | Storage | Global | Account-level S3 Block Public Access has all four settings on | AC-3, SC-7 | 2.1.4 |
| STO-02 | Storage | Regional | EBS encryption by default is enabled | SC-28 | 2.2.1 |
| EC2-01 | Compute | Regional | Each instance requires IMDSv2 (`HttpTokens=required`); WARN if hop limit is above 2 | CM-6, CM-7 | 5.6 |
| EC2-02 | Compute | Regional | Each instance's EBS volumes are encrypted (FAIL if not) with a customer-managed KMS key (WARN for `aws/ebs`); unattached volumes reported too | SC-28, SC-12 | 2.2.1 |
| EC2-03 | Compute | Regional | Each instance has no public IPv4 address | SC-7, AC-17 | |
| EC2-04 | Compute | Regional | Each running instance is managed by Systems Manager and online | CM-8, SI-2, AC-17 | |
| EC2-05 | Compute | Regional | Each instance has an IAM instance profile (WARN if not) | AC-6, IA-5 | 1.18 |
| NET-01 | Network | Regional | No security group allows `0.0.0.0/0` or `::/0` to port 22 or 3389 (including all-traffic rules) | SC-7, AC-17, CM-7 | 5.2, 5.3 |
| NET-02 | Network | Regional | Default security groups have no inbound or outbound rules (WARN) | SC-7, CM-7 | 5.4 |
| NET-03 | Network | Regional | No default VPC in the region (WARN) | SC-7, CM-7 | |
| NET-04 | Network | Regional | Every VPC has an active flow log | AU-12, SI-4 | 3.7 |
| BKP-01 | Backup | Regional | At least one AWS Backup plan exists | CP-9 | |
| BKP-02 | Backup | Regional | Each instance has an AWS Backup recovery point from the last 48 hours (FAIL if none, WARN if older) | CP-9, CP-10 | |
| BKP-03 | Backup | Regional | Backup vaults have Vault Lock (FAIL if unlocked with recovery points, WARN if unlocked and empty); mode and retention shown | CP-9, SI-7, AU-9 | |
| BKP-04 | Backup | Regional | Each backup plan has a copy action to a vault in another region | CP-6, CP-9 | |

CIS numbering follows CIS AWS Foundations Benchmark v3.0.0 and can shift between versions; a blank cell means the benchmark has no matching recommendation. `aws-posture-check --list-checks` prints the same table from the code.

## Install

Python 3.9 or later. boto3 is the only dependency.

```bash
git clone <this repository> && cd sop-library
python3 -m venv .venv && . .venv/bin/activate
pip install ./tools/aws-posture-check
aws-posture-check --version
```

`python3 -m aws_posture_check` works the same way once installed.

## Required permissions

Run it with a read-only identity, for example the `SecurityAudit` permission set given to `aws-auditors` in SOP-AWS-001 step 8. Either:

- attach the AWS managed policies **`SecurityAudit`** and **`ViewOnlyAccess`** (together they cover every call), or
- use the minimal custom policy in [`policy/aws-posture-check-readonly.json`](policy/aws-posture-check-readonly.json), which allows only these actions:

| Service | Actions |
|---|---|
| IAM | `GetAccountSummary`, `GetAccountPasswordPolicy`, `ListVirtualMFADevices`, `GenerateCredentialReport`, `GetCredentialReport` |
| IAM Identity Center | `sso:ListInstances` |
| CloudTrail | `DescribeTrails`, `GetTrailStatus`, `GetEventSelectors` |
| AWS Config | `DescribeConfigurationRecorders`, `DescribeConfigurationRecorderStatus` |
| GuardDuty | `ListDetectors`, `GetDetector` |
| Security Hub | `DescribeHub`, `GetEnabledStandards` |
| IAM Access Analyzer | `access-analyzer:ListAnalyzers` |
| S3 | `s3:GetAccountPublicAccessBlock` |
| EC2 | `GetEbsEncryptionByDefault`, `DescribeInstances`, `DescribeVolumes`, `DescribeSecurityGroups`, `DescribeVpcs`, `DescribeFlowLogs` |
| KMS | `ListAliases` (to tell `aws/ebs` from a customer-managed key) |
| Systems Manager | `DescribeInstanceInformation` |
| AWS Backup | `ListBackupPlans`, `GetBackupPlan`, `ListProtectedResources`, `ListBackupVaults` |

`sts:GetCallerIdentity` needs no permission. If a check shows ERROR with "Access denied", the detail names the API call that was refused. A service control policy that denies a region also shows up as ERROR for that region.

## Usage

Verify the account baseline after SOP-AWS-001:

```bash
aws-posture-check --profile auditor --regions us-east-1 --areas Identity Logging "Threat protection" Storage --fail-on fail
```

Verify hardened instances after SOP-AWS-002:

```bash
aws-posture-check --regions eu-central-1 --areas Compute Network Backup
```

Other examples:

```bash
# Everything, in both regions of the SOP-AWS-004 design, failing on warnings too
aws-posture-check --profile auditor --regions eu-central-1 eu-west-1 --fail-on warn

# Two checks only, evidence to a named folder, JSON to stdout
aws-posture-check --regions eu-central-1 --checks EC2-01 NET-01 --out ./evidence/CHG0012346 --format json
```

| Option | Meaning |
|---|---|
| `--profile NAME` | AWS CLI profile (for example an Identity Center profile after `aws sso login --profile auditor`). Default: the standard credential chain |
| `--regions R [R ...]` | Regions for regional checks. Default: the profile's region, else `us-east-1` |
| `--home-region R` | Region for global checks and IAM Identity Center. Default: the first of `--regions` |
| `--areas A [A ...]` | `Identity`, `Logging`, `"Threat protection"`, `Storage`, `Compute`, `Network`, `Backup` (case-insensitive). Default: all |
| `--checks ID [ID ...]` | Run only these check IDs |
| `--fail-on {fail,warn,never}` | Exit code threshold (see below). Default: `fail` |
| `--out DIR` | Evidence folder. Default: `./evidence/aws-posture-<account>-<UTC timestamp>` |
| `--format {text,json}` | stdout: a text summary (default) or the full `results.json` content |
| `--list-checks` | Print the check table and exit, without calling AWS |
| `-q`, `--quiet` | No progress lines on stderr |

## Output

Each run writes a folder such as `evidence/aws-posture-111122223333-20260115T120000Z/`:

| File | Content |
|---|---|
| `results.json` | `run` metadata (tool version, account ID, caller ARN, regions, home region, areas, check IDs, fail-on, exit code, UTC start and finish, Python and boto3 versions), `summary` counts by area and status, and every result |
| `results.csv` | One row per result: `check_id, area, title, status, region, resource_id, detail, remediation, nist_800_53, cis` |
| `report.md` | Run metadata, counts by area and status, then FAIL rows, WARN rows, ERROR rows and PASS rows, each with resource, detail, remediation and control mapping |
| `SHA256SUMS` | SHA-256 of the three files above, in `sha256sum` format |

Check the bundle has not been altered since the run:

```bash
cd evidence/aws-posture-111122223333-20260115T120000Z && sha256sum -c SHA256SUMS
```

The text summary on stdout shows counts by area and status, then each FAIL, WARN and ERROR row. The evidence contains account IDs, ARNs and resource names: store it with the change record, not in a public place.

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Run completed and nothing met the `--fail-on` threshold |
| 1 | `--fail-on fail`: at least one FAIL. `--fail-on warn`: at least one FAIL, WARN or ERROR. `--fail-on never` never returns 1 |
| 2 | Could not run: bad arguments, unknown profile, no or invalid credentials, or the evidence folder could not be written |

With the default `--fail-on fail`, ERROR results do not change the exit code, so read the ERROR section of the report: an ERROR is an unverified control, not a passed one. Use `--fail-on warn` in pipelines where every control must be proven.

## Notes and limits

- **Regional services.** GuardDuty, Security Hub, Access Analyzer, AWS Config, EBS default encryption and everything in Compute, Network and Backup are regional. List every region you use in `--regions`.
- **Identity Center** is looked for in the home region only. If it lives elsewhere, pass `--home-region`.
- **Organization trails** created in the management account appear in member accounts and count for LOG-01 to LOG-03.
- **BKP-02** needs a completed backup job, so a newly launched instance shows FAIL until its first recovery point exists.
- **EC2-02** reports the key type as unknown, and passes an encrypted volume, if `kms:ListAliases` is denied.
- The tool reads configuration state only; it does not review IAM policy content, bucket policies or findings inside GuardDuty and Security Hub.

## Development

Tests use the standard library only, with fake clients, so they need neither boto3 nor network access. From the repository root:

```bash
python3 -m unittest discover -s tools/aws-posture-check/tests
```

Checks live in `src/aws_posture_check/checks/`, one module per area. Each is a small function registered with `@register(id, area, title, scope, nist=..., cis=..., remediation=...)` that takes a context and a region and yields `outcome(status, resource_id, detail)` values. The runner turns any exception into an ERROR result.

## License

Code in this folder is MIT licensed: see [LICENSE](LICENSE). Copyright Rich Dieu. The runbook text elsewhere in this repository stays under CC BY 4.0.
