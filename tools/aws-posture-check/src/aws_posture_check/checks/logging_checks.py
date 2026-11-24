"""Logging: CloudTrail (account-wide) and AWS Config recorders (per region)."""

from ..core import (
    ERROR, FAIL, GLOBAL, PASS, REGIONAL, WARN, describe_error, outcome, register,
)

AREA = "Logging"


def trails(ctx):
    """Every trail visible from the home region, including trails homed in other regions."""
    return ctx.cached(
        "cloudtrail:trails",
        lambda: ctx.client("cloudtrail").describe_trails(includeShadowTrails=True).get("trailList", []),
    )


def multi_region_trails(ctx):
    return [t for t in trails(ctx) if t.get("IsMultiRegionTrail")]


def _trail_id(trail):
    return trail.get("TrailARN") or trail.get("Name", "trail")


def _trail_region(ctx, trail):
    return trail.get("HomeRegion") or ctx.home_region


def management_coverage(selectors):
    """Return 'all', 'partial' or 'none' for the management events a trail records."""
    covered = set()
    for es in selectors.get("EventSelectors") or []:
        if es.get("IncludeManagementEvents", True):
            rw = es.get("ReadWriteType", "All")
            covered |= {"read", "write"} if rw == "All" else {"read"} if rw == "ReadOnly" else {"write"}
    for adv in selectors.get("AdvancedEventSelectors") or []:
        fields = adv.get("FieldSelectors") or []
        category = [f for f in fields if f.get("Field") == "eventCategory"]
        if not any("Management" in (f.get("Equals") or []) for f in category):
            continue
        read_only = [f for f in fields if f.get("Field") == "readOnly"]
        if not read_only:
            covered |= {"read", "write"}
        for f in read_only:
            for v in f.get("Equals") or []:
                covered.add("read" if str(v).lower() == "true" else "write")
    if covered == {"read", "write"}:
        return "all"
    return "partial" if covered else "none"


NO_TRAIL = "No multi-region CloudTrail trail exists"


@register(
    "LOG-01", AREA, "A multi-region CloudTrail trail is logging all management events", GLOBAL,
    nist=("AU-2", "AU-12"), cis="3.1",
    remediation="aws cloudtrail create-trail --name account-trail --s3-bucket-name <bucket> --is-multi-region-trail "
                "--enable-log-file-validation --include-global-service-events; aws cloudtrail start-logging --name account-trail",
)
def cloudtrail_logging(ctx, region):
    mr = multi_region_trails(ctx)
    if not mr:
        yield outcome(FAIL, ctx.account_id, NO_TRAIL)
        return
    for trail in mr:
        tid, home = _trail_id(trail), _trail_region(ctx, trail)
        try:
            ct = ctx.client("cloudtrail", home)
            logging_on = bool(ct.get_trail_status(Name=tid).get("IsLogging"))
            coverage = management_coverage(ct.get_event_selectors(TrailName=tid))
        except Exception as exc:
            yield outcome(ERROR, tid, describe_error(exc), region=home)
            continue
        if not logging_on:
            yield outcome(FAIL, tid, "Multi-region trail exists but logging is stopped", region=home)
        elif coverage != "all":
            yield outcome(WARN, tid, "Trail is logging, but management events coverage is %s (needs read and write)"
                          % coverage, region=home)
        else:
            yield outcome(PASS, tid, "Multi-region trail is logging read and write management events", region=home)


@register(
    "LOG-02", AREA, "CloudTrail log file validation is enabled", GLOBAL,
    nist=("AU-9", "SI-7"), cis="3.2",
    remediation="aws cloudtrail update-trail --name <trail> --enable-log-file-validation",
)
def cloudtrail_validation(ctx, region):
    mr = multi_region_trails(ctx)
    if not mr:
        yield outcome(FAIL, ctx.account_id, NO_TRAIL)
        return
    for trail in mr:
        status = PASS if trail.get("LogFileValidationEnabled") else FAIL
        yield outcome(status, _trail_id(trail),
                      "Log file validation is %s" % ("enabled" if status == PASS else "disabled"),
                      region=_trail_region(ctx, trail))


@register(
    "LOG-03", AREA, "CloudTrail logs are encrypted with SSE-KMS", GLOBAL,
    nist=("AU-9", "SC-28"), cis="3.5",
    remediation="aws cloudtrail update-trail --name <trail> --kms-key-id <key-arn> (the key policy must allow CloudTrail).",
)
def cloudtrail_kms(ctx, region):
    mr = multi_region_trails(ctx)
    if not mr:
        yield outcome(FAIL, ctx.account_id, NO_TRAIL)
        return
    for trail in mr:
        key = trail.get("KmsKeyId")
        if key:
            yield outcome(PASS, _trail_id(trail), "Encrypted with %s" % key, region=_trail_region(ctx, trail))
        else:
            yield outcome(WARN, _trail_id(trail), "Logs use S3 default encryption, not SSE-KMS",
                          region=_trail_region(ctx, trail))


def _records_all(group):
    if not group:
        return True  # AWS default recording group records all supported types
    if group.get("allSupported"):
        return True
    strategy = (group.get("recordingStrategy") or {}).get("useOnly")
    return strategy == "ALL_SUPPORTED_RESOURCE_TYPES"


@register(
    "LOG-04", AREA, "AWS Config recorder is recording all resource types", REGIONAL,
    nist=("CM-8", "CA-7"), cis="3.3",
    remediation="AWS Config console, Get started (one-click setup) in this region: record all resource types "
                "(SOP-AWS-001 step 10).",
)
def config_recorder(ctx, region):
    cfg = ctx.client("config", region)
    recorders = cfg.describe_configuration_recorders().get("ConfigurationRecorders", [])
    if not recorders:
        yield outcome(FAIL, region, "No AWS Config configuration recorder in this region")
        return
    statuses = {s.get("name"): s for s in
                cfg.describe_configuration_recorder_status().get("ConfigurationRecordersStatus", [])}
    for rec in recorders:
        name = rec.get("name", "recorder")
        st = statuses.get(name, {})
        if not st.get("recording"):
            yield outcome(FAIL, name, "Recorder exists but is not recording")
        elif st.get("lastStatus") == "Failure" or st.get("lastStatus") == "FAILURE":
            yield outcome(WARN, name, "Recorder is on but its last recording attempt failed: %s"
                          % (st.get("lastErrorCode") or "unknown error"))
        elif not _records_all(rec.get("recordingGroup")):
            yield outcome(WARN, name, "Recorder is on but records only selected resource types")
        else:
            yield outcome(PASS, name, "Recording all supported resource types")
