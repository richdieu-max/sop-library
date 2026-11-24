"""Network: security groups, the default VPC and VPC flow logs (per region)."""

from ..core import FAIL, PASS, REGIONAL, WARN, outcome, paginate, register
from . import _ec2

AREA = "Network"
ADMIN_PORTS = (22, 3389)
OPEN_V4 = "0.0.0.0/0"
OPEN_V6 = "::/0"


def open_admin_ports(permission):
    """List of (port, cidr, protocol) where the rule exposes an admin port to the internet."""
    proto = str(permission.get("IpProtocol", ""))
    if proto not in ("-1", "tcp", "6", "udp", "17"):
        return []
    cidrs = [r.get("CidrIp") for r in permission.get("IpRanges") or [] if r.get("CidrIp") == OPEN_V4]
    cidrs += [r.get("CidrIpv6") for r in permission.get("Ipv6Ranges") or [] if r.get("CidrIpv6") == OPEN_V6]
    if not cidrs:
        return []
    lo, hi = permission.get("FromPort"), permission.get("ToPort")
    if proto == "-1" or lo is None or lo == -1:
        ports = list(ADMIN_PORTS)
    else:
        ports = [p for p in ADMIN_PORTS if lo <= p <= (hi if hi is not None else lo)]
    label = "all" if proto == "-1" else {"6": "tcp", "17": "udp"}.get(proto, proto)
    return [(p, c, label) for p in ports for c in cidrs]


@register(
    "NET-01", AREA, "No security group allows 0.0.0.0/0 or ::/0 to port 22 or 3389", REGIONAL,
    nist=("SC-7", "AC-17", "CM-7"), cis="5.2, 5.3",
    remediation="Remove the inbound rule (aws ec2 revoke-security-group-ingress) and use Session Manager instead of "
                "SSH or RDP from the internet.",
)
def open_admin_sg(ctx, region):
    groups = _ec2.security_groups(ctx, region)
    bad = 0
    for sg in groups:
        hits = []
        for perm in sg.get("IpPermissions") or []:
            hits.extend(open_admin_ports(perm))
        if hits:
            bad += 1
            text = ", ".join(sorted({"%s/%s from %s" % (p, proto, c) for p, c, proto in hits}))
            yield outcome(FAIL, sg.get("GroupId"), "%s (%s) allows %s" % (sg.get("GroupName"), sg.get("VpcId"), text))
    if not bad:
        yield outcome(PASS, region, "%d security group(s) checked; none open 22 or 3389 to the internet" % len(groups))


@register(
    "NET-02", AREA, "Default security groups allow no traffic", REGIONAL,
    nist=("SC-7", "CM-7"), cis="5.4",
    remediation="Remove every inbound and outbound rule from the default security group and use named groups instead.",
)
def default_sg(ctx, region):
    defaults = [g for g in _ec2.security_groups(ctx, region) if g.get("GroupName") == "default"]
    if not defaults:
        yield outcome(PASS, region, "No default security groups (no VPCs)")
        return
    for sg in defaults:
        n_in, n_out = len(sg.get("IpPermissions") or []), len(sg.get("IpPermissionsEgress") or [])
        if n_in or n_out:
            yield outcome(WARN, sg.get("GroupId"), "Default group in %s has %d inbound and %d outbound rule(s)"
                          % (sg.get("VpcId"), n_in, n_out))
        else:
            yield outcome(PASS, sg.get("GroupId"), "Default group in %s has no rules" % sg.get("VpcId"))


@register(
    "NET-03", AREA, "No default VPC in the region", REGIONAL,
    nist=("SC-7", "CM-7"), cis="",
    remediation="Delete the default VPC once nothing uses it (its subnets give instances a public IP by default). "
                "It can be recreated later with aws ec2 create-default-vpc.",
)
def default_vpc(ctx, region):
    defaults = [v for v in _ec2.vpcs(ctx, region) if v.get("IsDefault")]
    if not defaults:
        yield outcome(PASS, region, "No default VPC")
    for vpc in defaults:
        yield outcome(WARN, vpc.get("VpcId"), "Default VPC %s is present" % vpc.get("CidrBlock", ""))


@register(
    "NET-04", AREA, "VPC flow logs are active for every VPC", REGIONAL,
    nist=("AU-12", "SI-4"), cis="3.7",
    remediation="aws ec2 create-flow-logs --resource-type VPC --resource-ids <vpc-id> --traffic-type ALL "
                "--log-destination-type cloud-watch-logs --log-group-name <group> --deliver-logs-permission-arn <role-arn>",
)
def flow_logs(ctx, region):
    vpcs = _ec2.vpcs(ctx, region)
    if not vpcs:
        yield outcome(PASS, region, "No VPCs in this region")
        return
    active = {}
    for fl in paginate(ctx.client("ec2", region), "describe_flow_logs", "FlowLogs"):
        if fl.get("FlowLogStatus") == "ACTIVE":
            active.setdefault(fl.get("ResourceId"), []).append(fl.get("TrafficType", "?"))
    for vpc in vpcs:
        vid = vpc.get("VpcId")
        if vid in active:
            yield outcome(PASS, vid, "Active flow log(s), traffic type %s" % ", ".join(sorted(set(active[vid]))))
        else:
            yield outcome(FAIL, vid, "No active flow log%s" % (" (default VPC)" if vpc.get("IsDefault") else ""))
