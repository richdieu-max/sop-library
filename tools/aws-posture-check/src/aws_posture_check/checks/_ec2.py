"""Shared, cached EC2 inventory used by the Compute, Network and Backup checks."""

from ..core import paginate, tag_value

LIVE_STATES = ("pending", "running", "stopping", "stopped")


def instances(ctx, region):
    """Non-terminated instances in the region."""

    def load():
        found = []
        for reservation in paginate(ctx.client("ec2", region), "describe_instances", "Reservations"):
            for inst in reservation.get("Instances") or []:
                if (inst.get("State") or {}).get("Name") in LIVE_STATES:
                    found.append(inst)
        return found

    return ctx.cached(("ec2:instances", region), load)


def label(inst):
    name = tag_value(inst, "Name")
    return "%s (%s)" % (name, inst.get("InstanceId")) if name else inst.get("InstanceId")


def state(inst):
    return (inst.get("State") or {}).get("Name", "unknown")


def vpcs(ctx, region):
    return ctx.cached(("ec2:vpcs", region),
                      lambda: list(paginate(ctx.client("ec2", region), "describe_vpcs", "Vpcs")))


def security_groups(ctx, region):
    return ctx.cached(("ec2:sgs", region),
                      lambda: list(paginate(ctx.client("ec2", region), "describe_security_groups", "SecurityGroups")))
