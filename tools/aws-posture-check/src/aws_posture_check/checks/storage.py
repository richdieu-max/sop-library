"""Storage: account-level S3 Block Public Access and EBS encryption by default."""

from ..core import FAIL, GLOBAL, PASS, REGIONAL, error_code, outcome, register

AREA = "Storage"
BPA_SETTINGS = ("BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets")


@register(
    "STO-01", AREA, "S3 Block Public Access is on at account level (all four settings)", GLOBAL,
    nist=("AC-3", "SC-7"), cis="2.1.4",
    remediation="aws s3control put-public-access-block --account-id <account> --public-access-block-configuration "
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true",
)
def s3_account_bpa(ctx, region):
    try:
        cfg = ctx.client("s3control", region).get_public_access_block(AccountId=ctx.account_id) \
            .get("PublicAccessBlockConfiguration", {})
    except Exception as exc:
        if error_code(exc) == "NoSuchPublicAccessBlockConfiguration":
            yield outcome(FAIL, ctx.account_id, "No account-level Block Public Access configuration")
            return
        raise
    off = [s for s in BPA_SETTINGS if not cfg.get(s)]
    if off:
        yield outcome(FAIL, ctx.account_id, "Settings off: %s" % ", ".join(off))
    else:
        yield outcome(PASS, ctx.account_id, "All four Block Public Access settings are on")


@register(
    "STO-02", AREA, "EBS encryption by default is enabled", REGIONAL,
    nist=("SC-28",), cis="2.2.1",
    remediation="aws ec2 enable-ebs-encryption-by-default --region <region>",
)
def ebs_default_encryption(ctx, region):
    on = ctx.client("ec2", region).get_ebs_encryption_by_default().get("EbsEncryptionByDefault")
    if on:
        yield outcome(PASS, region, "EBS encryption by default is enabled")
    else:
        yield outcome(FAIL, region, "EBS encryption by default is disabled")
