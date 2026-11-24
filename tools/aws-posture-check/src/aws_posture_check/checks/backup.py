"""Backup: AWS Backup plans, protected EC2 instances, Vault Lock and cross-region copies (per region)."""

from ..core import ERROR, FAIL, PASS, REGIONAL, WARN, describe_error, outcome, paginate, parse_time, register
from . import _ec2

AREA = "Backup"
RECENT_BACKUP_HOURS = 48
AIR_GAPPED = "LOGICALLY_AIR_GAPPED_BACKUP_VAULT"


def plans(ctx, region):
    return ctx.cached(("backup:plans", region),
                      lambda: list(paginate(ctx.client("backup", region), "list_backup_plans", "BackupPlansList")))


@register(
    "BKP-01", AREA, "An AWS Backup plan exists", REGIONAL,
    nist=("CP-9",), cis="",
    remediation="aws backup create-backup-plan --backup-plan file://plan-prd.json, then create-backup-selection by tag "
                "(SOP-AWS-004 step 3).",
)
def backup_plan(ctx, region):
    found = plans(ctx, region)
    if not found:
        yield outcome(FAIL, region, "No AWS Backup plan in this region")
    for p in found:
        yield outcome(PASS, p.get("BackupPlanArn") or p.get("BackupPlanId"), "Plan %s" % p.get("BackupPlanName"))


@register(
    "BKP-02", AREA, "EC2 instances have a recovery point from the last %d hours" % RECENT_BACKUP_HOURS, REGIONAL,
    nist=("CP-9", "CP-10"), cis="",
    remediation="Tag the instance (for example Backup=daily) so a backup plan selection picks it up, then check the "
                "backup jobs in AWS Backup.",
)
def protected_instances(ctx, region):
    insts = _ec2.instances(ctx, region)
    if not insts:
        yield outcome(PASS, region, "No EC2 instances in this region")
        return
    last = {}
    for res in paginate(ctx.client("backup", region), "list_protected_resources", "Results"):
        arn = res.get("ResourceArn") or ""
        if ":instance/" in arn:
            last[arn.rsplit("/", 1)[-1]] = parse_time(res.get("LastBackupTime"))
    for inst in insts:
        iid = inst.get("InstanceId")
        who = "%s: " % _ec2.label(inst)
        if iid not in last:
            yield outcome(FAIL, iid, who + "No AWS Backup recovery point")
            continue
        when = last[iid]
        if when is None:
            yield outcome(WARN, iid, who + "Protected, but last backup time unknown")
            continue
        hours = int((ctx.now - when).total_seconds() // 3600)
        status = PASS if hours <= RECENT_BACKUP_HOURS else WARN
        yield outcome(status, iid, who + "Last backup %s (%d hours ago)" % (when.strftime("%Y-%m-%d %H:%M UTC"), hours))


@register(
    "BKP-03", AREA, "Backup vaults are protected by Vault Lock", REGIONAL,
    nist=("CP-9", "SI-7", "AU-9"), cis="",
    remediation="aws backup put-backup-vault-lock-configuration --backup-vault-name <vault> --min-retention-days 7 "
                "--max-retention-days 400 (governance mode first; compliance mode after a passed restore test).",
)
def vault_lock(ctx, region):
    vaults = list(paginate(ctx.client("backup", region), "list_backup_vaults", "BackupVaultList"))
    if not vaults:
        yield outcome(WARN, region, "No backup vaults in this region")
        return
    for v in vaults:
        name = v.get("BackupVaultArn") or v.get("BackupVaultName")
        points = v.get("NumberOfRecoveryPoints", 0) or 0
        if v.get("VaultType") == AIR_GAPPED:
            yield outcome(PASS, name, "Logically air-gapped vault (locked by design)")
        elif v.get("Locked"):
            mode = "compliance" if v.get("LockDate") else "governance"
            yield outcome(PASS, name, "Vault Lock in %s mode, retention %s to %s days, %d recovery point(s)"
                          % (mode, v.get("MinRetentionDays", "?"), v.get("MaxRetentionDays", "?"), points))
        elif points:
            yield outcome(FAIL, name, "Not locked and holds %d recovery point(s)" % points)
        else:
            yield outcome(WARN, name, "Not locked (vault is empty)")


@register(
    "BKP-04", AREA, "Backup plans copy recovery points to another region", REGIONAL,
    nist=("CP-6", "CP-9"), cis="",
    remediation="Add a copy action to the plan rule with DestinationBackupVaultArn set to a locked vault in the "
                "recovery region (SOP-AWS-004 step 3).",
)
def cross_region_copy(ctx, region):
    found = plans(ctx, region)
    if not found:
        yield outcome(FAIL, region, "No AWS Backup plan in this region, so no copy rule")
        return
    bk = ctx.client("backup", region)
    for p in found:
        pid = p.get("BackupPlanId")
        arn = p.get("BackupPlanArn") or pid
        try:
            rules = (bk.get_backup_plan(BackupPlanId=pid).get("BackupPlan") or {}).get("Rules") or []
        except Exception as exc:
            yield outcome(ERROR, arn, describe_error(exc))
            continue
        dests = set()
        for rule in rules:
            for action in rule.get("CopyActions") or []:
                parts = str(action.get("DestinationBackupVaultArn", "")).split(":")
                if len(parts) > 3 and parts[3] and parts[3] != region:
                    dests.add(parts[3])
        if dests:
            yield outcome(PASS, arn, "Plan %s copies to %s" % (p.get("BackupPlanName"), ", ".join(sorted(dests))))
        else:
            yield outcome(FAIL, arn, "Plan %s has no cross-region copy action" % p.get("BackupPlanName"))
