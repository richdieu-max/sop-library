"""Threat protection: GuardDuty, Security Hub and IAM Access Analyzer (per region)."""

from ..core import FAIL, PASS, REGIONAL, WARN, error_code, outcome, paginate, register

AREA = "Threat protection"


@register(
    "THR-01", AREA, "GuardDuty detector is enabled", REGIONAL,
    nist=("SI-4", "RA-5"), cis="",
    remediation="aws guardduty create-detector --enable --finding-publishing-frequency FIFTEEN_MINUTES --region <region> "
                "(detectors are regional: repeat in every region in use).",
)
def guardduty(ctx, region):
    gd = ctx.client("guardduty", region)
    ids = list(paginate(gd, "list_detectors", "DetectorIds"))
    if not ids:
        yield outcome(FAIL, region, "No GuardDuty detector in this region")
        return
    for detector_id in ids:
        status = gd.get_detector(DetectorId=detector_id).get("Status")
        if status == "ENABLED":
            yield outcome(PASS, detector_id, "Detector is enabled")
        else:
            yield outcome(FAIL, detector_id, "Detector status is %s" % status)


NOT_ENABLED_CODES = {"InvalidAccessException", "ResourceNotFoundException"}


@register(
    "THR-02", AREA, "Security Hub is enabled with at least one standard", REGIONAL,
    nist=("CA-7", "SI-4", "RA-5"), cis="4.16",
    remediation="aws securityhub enable-security-hub --enable-default-standards --region <region>",
)
def security_hub(ctx, region):
    sh = ctx.client("securityhub", region)
    try:
        hub = sh.describe_hub()
    except Exception as exc:
        if error_code(exc) in NOT_ENABLED_CODES:
            yield outcome(FAIL, region, "Security Hub is not enabled in this region")
            return
        raise
    hub_arn = hub.get("HubArn", region)
    standards = [s for s in paginate(sh, "get_enabled_standards", "StandardsSubscriptions")
                 if s.get("StandardsStatus") in ("READY", "INCOMPLETE", "PENDING")]
    if not standards:
        yield outcome(WARN, hub_arn, "Security Hub is enabled but no standards are enabled")
        return
    names = sorted({s.get("StandardsArn", "").split(":")[-1] for s in standards})
    yield outcome(PASS, hub_arn, "Enabled standards: %s" % ", ".join(names))


@register(
    "THR-03", AREA, "IAM Access Analyzer (external access) is active", REGIONAL,
    nist=("AC-6", "CA-7"), cis="1.20",
    remediation="aws accessanalyzer create-analyzer --analyzer-name account --type ACCOUNT --region <region>",
)
def access_analyzer(ctx, region):
    analyzers = [a for a in paginate(ctx.client("accessanalyzer", region), "list_analyzers", "analyzers")
                 if a.get("type") in ("ACCOUNT", "ORGANIZATION")]
    active = [a for a in analyzers if a.get("status") == "ACTIVE"]
    if active:
        for a in active:
            yield outcome(PASS, a.get("arn") or a.get("name"), "%s analyzer is active" % a.get("type"))
    elif analyzers:
        yield outcome(FAIL, analyzers[0].get("arn") or analyzers[0].get("name"),
                      "Analyzer exists but status is %s" % analyzers[0].get("status"))
    else:
        yield outcome(FAIL, region, "No external access analyzer in this region")
