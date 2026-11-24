"""Compute: EC2 instance hardening from SOP-AWS-002 (per region)."""

from ..core import FAIL, PASS, REGIONAL, WARN, outcome, paginate, register
from . import _ec2

AREA = "Compute"
NO_INSTANCES = "No EC2 instances in this region"


def _prefix(inst):
    return "%s: " % _ec2.label(inst)


@register(
    "EC2-01", AREA, "Instance requires IMDSv2 (session tokens)", REGIONAL,
    nist=("CM-6", "CM-7"), cis="5.6",
    remediation="aws ec2 modify-instance-metadata-options --instance-id <id> --http-tokens required "
                "--http-put-response-hop-limit 1; set the regional default with modify-instance-metadata-defaults.",
)
def imdsv2(ctx, region):
    insts = _ec2.instances(ctx, region)
    if not insts:
        yield outcome(PASS, region, NO_INSTANCES)
        return
    for inst in insts:
        md = inst.get("MetadataOptions") or {}
        iid = inst.get("InstanceId")
        if md.get("HttpEndpoint") == "disabled":
            yield outcome(PASS, iid, _prefix(inst) + "Instance metadata endpoint is disabled")
        elif md.get("HttpTokens") != "required":
            yield outcome(FAIL, iid, _prefix(inst) + "IMDSv1 allowed (HttpTokens=%s)" % md.get("HttpTokens", "unknown"))
        elif (md.get("HttpPutResponseHopLimit") or 1) > 2:
            yield outcome(WARN, iid, _prefix(inst) + "IMDSv2 required, but hop limit is %s (use 1, or 2 for containers)"
                          % md.get("HttpPutResponseHopLimit"))
        else:
            yield outcome(PASS, iid, _prefix(inst) + "IMDSv2 required, hop limit %s" % md.get("HttpPutResponseHopLimit", 1))


def _aws_managed_ebs_key(ctx, region):
    """Key id behind alias/aws/ebs, or None if it cannot be read."""
    def load():
        for alias in paginate(ctx.client("kms", region), "list_aliases", "Aliases"):
            if alias.get("AliasName") == "alias/aws/ebs":
                return alias.get("TargetKeyId")
        return None
    try:
        return ctx.cached(("kms:aws-ebs", region), load)
    except Exception:
        return None


def _volume_status(vol, managed_key):
    """(status, text) for one volume."""
    vid = vol.get("VolumeId")
    if not vol.get("Encrypted"):
        return FAIL, "%s unencrypted" % vid
    key = vol.get("KmsKeyId") or ""
    if managed_key and key.split("/")[-1] == managed_key:
        return WARN, "%s encrypted with the AWS managed key aws/ebs" % vid
    return PASS, "%s encrypted with %s" % (vid, key.split("/")[-1] or "KMS")


_RANK = {PASS: 0, WARN: 1, FAIL: 2}


@register(
    "EC2-02", AREA, "EBS volumes are encrypted with a customer-managed KMS key", REGIONAL,
    nist=("SC-28", "SC-12"), cis="2.2.1",
    remediation="Snapshot the volume, copy the snapshot with --encrypted --kms-key-id alias/<your-key>, create a volume "
                "from it and swap it in. Enable EBS encryption by default with your key for new volumes.",
)
def volume_encryption(ctx, region):
    insts = _ec2.instances(ctx, region)
    volumes = {v.get("VolumeId"): v for v in paginate(ctx.client("ec2", region), "describe_volumes", "Volumes")}
    if not insts and not volumes:
        yield outcome(PASS, region, "No EC2 instances or EBS volumes in this region")
        return
    managed_key = _aws_managed_ebs_key(ctx, region) if volumes else None
    attached = set()
    for inst in insts:
        vids = [m.get("Ebs", {}).get("VolumeId") for m in inst.get("BlockDeviceMappings") or [] if m.get("Ebs")]
        attached.update(vids)
        parts = [_volume_status(volumes[v], managed_key) if v in volumes else (WARN, "%s not found" % v) for v in vids]
        if not parts:
            yield outcome(PASS, inst.get("InstanceId"), _prefix(inst) + "No EBS volumes attached")
            continue
        worst = max((p[0] for p in parts), key=_RANK.get)
        yield outcome(worst, inst.get("InstanceId"), _prefix(inst) + "; ".join(p[1] for p in parts))
    for vid, vol in sorted(volumes.items()):
        if vid in attached:
            continue
        status, text = _volume_status(vol, managed_key)
        yield outcome(status, vid, "Volume not attached to a live instance: " + text)


def _public_ips(inst):
    ips = set()
    if inst.get("PublicIpAddress"):
        ips.add(inst["PublicIpAddress"])
    for eni in inst.get("NetworkInterfaces") or []:
        ip = (eni.get("Association") or {}).get("PublicIp")
        if ip:
            ips.add(ip)
    return sorted(ips)


@register(
    "EC2-03", AREA, "Instance has no public IP address", REGIONAL,
    nist=("SC-7", "AC-17"), cis="",
    remediation="Relaunch in a private subnet with --no-associate-public-ip-address, release any Elastic IP, and "
                "publish through a load balancer; reach the instance with Session Manager.",
)
def public_ip(ctx, region):
    insts = _ec2.instances(ctx, region)
    if not insts:
        yield outcome(PASS, region, NO_INSTANCES)
        return
    for inst in insts:
        ips = _public_ips(inst)
        if ips:
            yield outcome(FAIL, inst.get("InstanceId"), _prefix(inst) + "Public IP %s" % ", ".join(ips))
        else:
            yield outcome(PASS, inst.get("InstanceId"), _prefix(inst) + "No public IP")


@register(
    "EC2-04", AREA, "Instance is managed by Systems Manager", REGIONAL,
    nist=("CM-8", "SI-2", "AC-17"), cis="",
    remediation="Attach an instance profile with AmazonSSMManagedInstanceCore and give the subnet a route to the "
                "ssm, ssmmessages and ec2messages endpoints (SOP-AWS-002 troubleshooting).",
)
def ssm_managed(ctx, region):
    insts = _ec2.instances(ctx, region)
    if not insts:
        yield outcome(PASS, region, NO_INSTANCES)
        return
    managed = {i.get("InstanceId"): i.get("PingStatus")
               for i in paginate(ctx.client("ssm", region), "describe_instance_information", "InstanceInformationList")}
    for inst in insts:
        iid, st = inst.get("InstanceId"), _ec2.state(inst)
        ping = managed.get(iid)
        if st == "running":
            if ping == "Online":
                yield outcome(PASS, iid, _prefix(inst) + "SSM agent online")
            elif ping:
                yield outcome(WARN, iid, _prefix(inst) + "Registered with SSM but ping status is %s" % ping)
            else:
                yield outcome(FAIL, iid, _prefix(inst) + "Running but not managed by Systems Manager")
        elif ping:
            yield outcome(PASS, iid, _prefix(inst) + "Instance is %s; registered with SSM" % st)
        else:
            yield outcome(WARN, iid, _prefix(inst) + "Instance is %s and not registered with SSM" % st)


@register(
    "EC2-05", AREA, "Instance has an IAM instance profile (no keys on disk)", REGIONAL,
    nist=("AC-6", "IA-5"), cis="1.18",
    remediation="aws ec2 associate-iam-instance-profile --instance-id <id> --iam-instance-profile Name=<profile> "
                "(AmazonSSMManagedInstanceCore and CloudWatchAgentServerPolicy only).",
)
def instance_profile(ctx, region):
    insts = _ec2.instances(ctx, region)
    if not insts:
        yield outcome(PASS, region, NO_INSTANCES)
        return
    for inst in insts:
        prof = (inst.get("IamInstanceProfile") or {}).get("Arn")
        if prof:
            yield outcome(PASS, inst.get("InstanceId"), _prefix(inst) + "Instance profile %s" % prof.split("/")[-1])
        else:
            yield outcome(WARN, inst.get("InstanceId"), _prefix(inst) + "No instance profile attached")
