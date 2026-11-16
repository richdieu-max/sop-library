# SOP-AWS-002 · Deploying a hardened EC2 instance in a data-residency region

Build a production Linux or Windows instance with no public IP, IMDSv2 required, encrypted volumes, Session Manager access, backup and monitoring. Then keep the instance, and everything that supports it, inside one approved region with a service control policy. The launch wizard's defaults make the first instance work, not pass an audit: with a default subnet the wizard assigns a public IP, and its suggested security group opens SSH to `0.0.0.0/0`. This is the AWS counterpart of [SOP-AZ-002](../azure-procedures/SOP-AZ-002-hardened-azure-vm-data-residency-region.md).

**Family:** AWS procedures · **Covers:** the console wizard section by section, the same build with the AWS CLI, the region guardrail, verification and rollback · **Does not cover:** load balancer and WAF design, AMI pipelines (EC2 Image Builder), or cross-region DR (see [SOP-AWS-004](SOP-AWS-004-multi-region-backup-disaster-recovery.md)).

## Shape

![Administrator reaches instances in private subnets of two Availability Zones only through Systems Manager Session Manager over VPC endpoints; an Application Load Balancer in public subnets fronts them; AWS Backup, CloudWatch and KMS sit in the same region, and an SCP denies every other region](diagrams/sop-aws-002-1.svg)

The worked example uses Europe (Frankfurt), `eu-central-1`, with one instance per Availability Zone behind a load balancer. Choosing the region is necessary but not enough. Snapshots, backups, logs and AMI copies must stay in that region too, and a service control policy must stop anyone creating resources elsewhere. Data residency is not data sovereignty: a Frankfurt region keeps data stored in Germany, but it does not change which laws can compel the provider.

| Layer | Controls | Stops |
|---|---|---|
| Organization | SCP denying regions outside the approved list (global services exempt) | Workloads, snapshots and copies outside the region |
| Network | Private subnets, no public IP, security group allows only the load balancer | SSH and RDP scans |
| Access | Session Manager over VPC endpoints, no inbound 22 or 3389, sessions logged | Key pairs on laptops, bastion hosts |
| Instance metadata | IMDSv2 required, hop limit 1 (2 for containers) | SSRF bugs stealing instance credentials |
| Storage | EBS encrypted with a customer-managed KMS key | Volumes or snapshots readable if shared or copied |
| Operate | Instance profile, AWS Backup plan, CloudWatch agent, Patch Manager | Keys on disk, no backup, no logs, no patches |

## Before you start

| Item | Requirement |
|---|---|
| Build | An Identity Center permission set with EC2, IAM pass-role for the instance profile, and KMS key use, as a time-boxed assignment |
| Network | VPC `vpc-prd-euc1` with private subnets in two AZs (for example `10.30.1.0/24`, `10.30.2.0/24`), no internet gateway route from them, and interface endpoints for `ssm`, `ssmmessages` and `ec2messages` (plus `logs` and `kms`) |
| Instance profile | Role with `AmazonSSMManagedInstanceCore` and `CloudWatchAgentServerPolicy`, nothing else |
| Keys | A customer-managed KMS key `alias/ebs-prd-euc1` with rotation on |
| Guardrail | The region SCP in place at the OU, owned by the platform team, not the instance builder |
| Change | Approved change `CHG0012346`; names like `web-prd-euc1-01`; an AMI you trust (AWS-published, or your own golden image) |

## Steps (console)

Open **EC2 › Launch instance**. Work through every section; do not skip to **Launch** after the AMI.

1. **Name and tags.** `web-prd-euc1-01`, plus `Environment=prd`, `DataClass=confidential`, `Backup=daily`. AWS Backup selects by the `Backup` tag.
2. **AMI and type.** The approved AMI; for example `m7i.large`.
3. **Key pair.** **Proceed without a key pair.** Access is through Session Manager.
4. **Network settings › Edit.** VPC `vpc-prd-euc1`, a **private** subnet, **Auto-assign public IP: Disable**. Security group: create `sg-web-prd`, with no inbound rule from the internet; inbound 443 only from the load balancer's security group (add it after the ALB exists).
5. **Storage.** gp3, **Encrypted: Yes**, KMS key `alias/ebs-prd-euc1`, delete on termination for the root volume only. Add a data volume for application data, encrypted the same way.
6. **Advanced details.** IAM instance profile `ec2-ssm-cw`; **Metadata accessible: Enabled**, **Metadata version: V2 only (token required)**, **hop limit: 1**; termination protection on; detailed CloudWatch monitoring on.
7. **Launch**, then repeat in the second AZ's subnet.

![IMDSv1 versus IMDSv2: a request forwarded by an SSRF bug gets credentials from IMDSv1 but is refused by IMDSv2 because it carries no session token from a PUT, and a hop limit of 1 stops the token leaving the instance; alongside, the three layers that keep data in the region: the SCP, region-locked backups and the KMS key's own region](diagrams/sop-aws-002-2.svg)

## Steps (CLI)

```bash
REGION=eu-central-1
aws ec2 run-instances --region $REGION \
  --image-id ami-0123456789abcdef0 --instance-type m7i.large \
  --subnet-id subnet-0aaaaaaaaaaaaaaa1 --security-group-ids sg-0bbbbbbbbbbbbbbb1 \
  --no-associate-public-ip-address \
  --iam-instance-profile Name=ec2-ssm-cw \
  --metadata-options HttpTokens=required,HttpPutResponseHopLimit=1,HttpEndpoint=enabled \
  --block-device-mappings 'DeviceName=/dev/xvda,Ebs={VolumeSize=30,VolumeType=gp3,Encrypted=true,KmsKeyId=alias/ebs-prd-euc1,DeleteOnTermination=true}' \
  --disable-api-termination --monitoring Enabled=true \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=web-prd-euc1-01},{Key=Environment,Value=prd},{Key=Backup,Value=daily}]'

# Make IMDSv2 the default for every new instance in the region
aws ec2 modify-instance-metadata-defaults --region $REGION --http-tokens required --http-put-response-hop-limit 1

# Fix an existing instance that still allows IMDSv1
aws ec2 modify-instance-metadata-options --region $REGION --instance-id i-0a1b2c3d4e5f60001 --http-tokens required
```

### Region guardrail (SCP, at the OU)

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyOutsideApprovedRegions",
    "Effect": "Deny",
    "NotAction": ["iam:*", "organizations:*", "sts:*", "support:*", "budgets:*", "cloudfront:*",
                  "route53:*", "waf:*", "health:*", "trustedadvisor:*", "account:*", "sso:*"],
    "Resource": "*",
    "Condition": {
      "StringNotEquals": {"aws:RequestedRegion": ["eu-central-1"]},
      "ArnNotLike": {"aws:PrincipalARN": "arn:aws:iam::*:role/platform-breakglass"}
    }
  }]
}
```

Global services run their control plane in `us-east-1`, so they are exempt through `NotAction`. Test a new SCP on a sandbox OU first: a deny in an SCP cannot be overridden by any permission in the account.

## Verify

1. **Systems Manager › Fleet Manager** lists the instance as managed; **Session Manager › Start session** opens a shell without any inbound port.
2. `aws ec2 describe-instances --instance-ids i-... --query 'Reservations[].Instances[].{IMDS:MetadataOptions.HttpTokens,PublicIp:PublicIpAddress}'` returns `required` and `null`.
3. Launching any resource in another region as a normal role fails with `UnauthorizedOperation`, and the message names the SCP.
4. `aws-posture-check --regions eu-central-1 --areas Compute Network Backup` shows the instances as PASS.

## Roll back

Termination protection is on, so remove it deliberately (`modify-instance-attribute --no-disable-api-termination`), take a final AWS Backup recovery point, then terminate. Encrypted snapshots stay readable only while the KMS key exists. Schedule key deletion only after the retention period of every backup that uses it has ended.

## Troubleshooting

| Symptom | Cause and fix |
|---|---|
| Instance not in Fleet Manager | No route to SSM: the interface endpoints are missing, or their security group does not allow 443 from the instance; or the instance profile lacks `AmazonSSMManagedInstanceCore` |
| An application broke after IMDSv2 was required | An old SDK or agent still uses IMDSv1; update it, or temporarily allow IMDSv1 on that instance and track it as an exception |
| A container on the instance cannot get credentials | Hop limit 1 stops the token crossing the container's network hop; set 2 on container hosts only |
| `UnauthorizedOperation` in the approved region | A service is missing from the SCP's `NotAction` list (often a new global service), or the request goes to a global endpoint |

## Control mapping

| Framework | Reference | How this supports it |
|---|---|---|
| NIST SP 800-53 R5 | SC-7, AC-17 | No public IP; access only through logged Session Manager sessions |
| | SC-28, SC-12 | EBS encryption with a customer-managed, rotated KMS key |
| | CM-6, CM-7 | IMDSv2, no key pairs, minimal instance profile |
| | SA-9(5), SC-7 | Processing and storage kept in the approved region by SCP |
| | CP-9, SI-2, AU-12 | AWS Backup by tag, Patch Manager, CloudWatch agent |
| NIST CSF 2.0 | PR.PS-01, PR.DS-01, PR.IR-01 | Secure configuration, data at rest, protected networks |
| CIS AWS Foundations Benchmark | 5.x networking, 2.2 EBS encryption | No admin ports from the internet; volumes encrypted |
