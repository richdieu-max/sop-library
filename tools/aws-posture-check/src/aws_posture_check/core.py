"""Core types: statuses, the check registry, the read-only client guard and the runner.

Nothing in this module imports boto3. Checks receive a ``Context`` whose client
factory can be a real boto3 session or a set of fake clients in unit tests.
"""

import time
from collections import namedtuple
from datetime import datetime, timezone

PASS = "PASS"
WARN = "WARN"
FAIL = "FAIL"
ERROR = "ERROR"
STATUSES = (PASS, WARN, FAIL, ERROR)

AREAS = (
    "Identity",
    "Logging",
    "Threat protection",
    "Storage",
    "Compute",
    "Network",
    "Backup",
)

GLOBAL = "global"
REGIONAL = "regional"

# --------------------------------------------------------------------------
# Areas
# --------------------------------------------------------------------------

_AREA_ALIASES = {a.lower(): a for a in AREAS}
_AREA_ALIASES.update(
    {
        "threat": "Threat protection",
        "threat-protection": "Threat protection",
        "threat_protection": "Threat protection",
        "threatprotection": "Threat protection",
    }
)


def normalise_area(name):
    """Return the canonical area name for ``name`` (case-insensitive), or raise ValueError."""
    key = " ".join(str(name).split()).lower()
    if key in _AREA_ALIASES:
        return _AREA_ALIASES[key]
    raise ValueError(
        "unknown area %r; choose from: %s" % (name, ", ".join('"%s"' % a for a in AREAS))
    )


# --------------------------------------------------------------------------
# Results and the registry
# --------------------------------------------------------------------------

Outcome = namedtuple("Outcome", "status resource_id detail remediation region")
Outcome.__new__.__defaults__ = (None, None)


def outcome(status, resource_id, detail, remediation=None, region=None):
    """What a check function yields for one resource."""
    if status not in STATUSES:
        raise ValueError("bad status %r" % status)
    return Outcome(status, str(resource_id), str(detail), remediation, region)


class Result(object):
    """One row of the evidence: a check applied to one resource in one region."""

    __slots__ = (
        "check_id", "area", "title", "status", "region", "resource_id",
        "detail", "remediation", "nist", "cis",
    )

    FIELDS = (
        "check_id", "area", "title", "status", "region", "resource_id",
        "detail", "remediation", "nist", "cis",
    )

    def __init__(self, check_id, area, title, status, region, resource_id,
                 detail, remediation, nist, cis):
        self.check_id = check_id
        self.area = area
        self.title = title
        self.status = status
        self.region = region
        self.resource_id = resource_id
        self.detail = detail
        self.remediation = remediation
        self.nist = tuple(nist)
        self.cis = cis

    def to_dict(self):
        d = {f: getattr(self, f) for f in self.FIELDS}
        d["nist"] = list(self.nist)
        return d

    def __repr__(self):
        return "Result(%s %s %s %s)" % (self.check_id, self.status, self.region, self.resource_id)


class Check(object):
    __slots__ = ("check_id", "area", "title", "scope", "nist", "cis", "remediation", "func")

    def __init__(self, check_id, area, title, scope, nist, cis, remediation, func):
        self.check_id = check_id
        self.area = area
        self.title = title
        self.scope = scope
        self.nist = tuple(nist)
        self.cis = cis
        self.remediation = remediation
        self.func = func


REGISTRY = []


def register(check_id, area, title, scope, nist, cis="", remediation=""):
    """Decorator that adds a check function to the registry.

    The function is called as ``func(ctx, region)`` and yields ``Outcome``
    values (use ``outcome()``). Global checks are called once with the home
    region; regional checks once per requested region.
    """
    if area not in AREAS:
        raise ValueError("unknown area %r" % area)
    if scope not in (GLOBAL, REGIONAL):
        raise ValueError("unknown scope %r" % scope)

    def decorator(func):
        if any(c.check_id == check_id for c in REGISTRY):
            raise ValueError("duplicate check id %s" % check_id)
        REGISTRY.append(Check(check_id, area, title, scope, nist, cis, remediation, func))
        return func

    return decorator


def all_checks():
    """Registered checks in report order (area order, then id)."""
    from . import checks  # noqa: F401  (importing registers every check)

    order = {a: i for i, a in enumerate(AREAS)}
    return sorted(REGISTRY, key=lambda c: (order[c.area], c.check_id))


def select_checks(areas=None, check_ids=None):
    selected = all_checks()
    if areas:
        wanted = set(areas)
        selected = [c for c in selected if c.area in wanted]
    if check_ids:
        ids = {i.upper() for i in check_ids}
        unknown = ids - {c.check_id for c in all_checks()}
        if unknown:
            raise ValueError("unknown check id(s): %s" % ", ".join(sorted(unknown)))
        selected = [c for c in selected if c.check_id in ids]
    return selected


# --------------------------------------------------------------------------
# Read-only guard
# --------------------------------------------------------------------------

READ_ONLY_PREFIXES = ("describe_", "get_", "list_")
READ_ONLY_EXTRA = frozenset({"generate_credential_report"})
_PASSTHROUGH = frozenset({"can_paginate", "meta", "exceptions"})


class ReadOnlyViolation(RuntimeError):
    """Raised if code tries to call an API that is not Describe, Get or List."""


def is_read_only_operation(name):
    return name.startswith(READ_ONLY_PREFIXES) or name in READ_ONLY_EXTRA


class ReadOnlyClient(object):
    """Wraps a boto3 (or fake) client and refuses every non read-only operation."""

    def __init__(self, client, service):
        self._client = client
        self._service = service

    def get_paginator(self, operation_name):
        if not is_read_only_operation(operation_name):
            raise ReadOnlyViolation("%s.%s is not a read-only operation" % (self._service, operation_name))
        return self._client.get_paginator(operation_name)

    def __getattr__(self, name):
        if name in _PASSTHROUGH:
            return getattr(self._client, name)
        if name.startswith("_") or not is_read_only_operation(name) or name in ("get_waiter",):
            raise ReadOnlyViolation("%s.%s is not a read-only operation" % (self._service, name))
        return getattr(self._client, name)


# --------------------------------------------------------------------------
# Errors and helpers
# --------------------------------------------------------------------------

ACCESS_DENIED_CODES = frozenset(
    {
        "AccessDenied",
        "AccessDeniedException",
        "UnauthorizedOperation",
        "UnauthorizedAccess",
        "UnauthorizedException",
        "AuthorizationError",
        "AuthorizationErrorException",
        "UnrecognizedClientException",
        "InvalidClientTokenId",
        "AuthFailure",
    }
)


def error_code(exc):
    """The AWS error code of a botocore ClientError (or a fake), else None."""
    resp = getattr(exc, "response", None)
    if isinstance(resp, dict):
        return (resp.get("Error") or {}).get("Code")
    return None


def describe_error(exc):
    code = error_code(exc)
    op = getattr(exc, "operation_name", None) or "the API"
    if code in ACCESS_DENIED_CODES:
        return ("Access denied calling %s (%s). Grant the read-only permissions listed in "
                "policy/aws-posture-check-readonly.json." % (op, code))
    if code:
        msg = ((getattr(exc, "response", None) or {}).get("Error") or {}).get("Message") or ""
        return "API error calling %s: %s %s" % (op, code, msg)
    return "Could not complete the check: %s: %s" % (type(exc).__name__, exc)


def paginate(client, operation, key, **kwargs):
    """Yield every item under ``key`` across all pages of ``operation``."""
    can = getattr(client, "can_paginate", None)
    if can is not None and can(operation):
        for page in client.get_paginator(operation).paginate(**kwargs):
            for item in page.get(key) or []:
                yield item
    else:
        for item in getattr(client, operation)(**kwargs).get(key) or []:
            yield item


def parse_time(value):
    """Parse an AWS timestamp (datetime or ISO 8601 string) to an aware UTC datetime, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = str(value).strip()
    if not text or text.lower() in ("n/a", "no_information", "not_supported", "none"):
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def days_between(earlier, later):
    return int((later - earlier).total_seconds() // 86400)


def tag_value(resource, key):
    for tag in resource.get("Tags") or []:
        if tag.get("Key") == key:
            return tag.get("Value")
    return None


# --------------------------------------------------------------------------
# Context and runner
# --------------------------------------------------------------------------

class Context(object):
    """Everything a check needs: read-only clients, account facts and a shared cache.

    ``client_factory(service, region)`` returns a client; it is wrapped in
    ``ReadOnlyClient`` so a check cannot make a change even by mistake.
    """

    def __init__(self, client_factory, account_id, regions, home_region=None,
                 caller_arn="", now=None, sleep=time.sleep):
        self._factory = client_factory
        self._clients = {}
        self._cache = {}
        self.account_id = account_id
        self.caller_arn = caller_arn
        self.regions = list(regions)
        self.home_region = home_region or self.regions[0]
        self.now = now or datetime.now(timezone.utc)
        self.sleep = sleep

    def client(self, service, region=None):
        region = region or self.home_region
        key = (service, region)
        if key not in self._clients:
            self._clients[key] = ReadOnlyClient(self._factory(service, region), service)
        return self._clients[key]

    def cached(self, key, loader):
        """Run ``loader`` once per key. Exceptions are cached and re-raised too."""
        if key not in self._cache:
            try:
                self._cache[key] = (True, loader())
            except Exception as exc:  # cached so every dependent check reports the same ERROR
                self._cache[key] = (False, exc)
        ok, value = self._cache[key]
        if ok:
            return value
        raise value


def _region_label(check, region):
    return GLOBAL if check.scope == GLOBAL else region


def run_check(ctx, check, region):
    """Run one check in one region. Never raises: failures become ERROR results."""
    label = _region_label(check, region)
    results = []

    def add(o):
        results.append(Result(
            check.check_id, check.area, check.title, o.status, o.region or label,
            o.resource_id, o.detail, o.remediation or check.remediation, check.nist, check.cis,
        ))

    try:
        for o in check.func(ctx, region) or []:
            add(o)
    except Exception as exc:  # includes ReadOnlyViolation: the call was blocked, not made
        add(outcome(ERROR, ctx.account_id if check.scope == GLOBAL else region, describe_error(exc)))
    if not results:
        add(outcome(ERROR, ctx.account_id, "Check returned no result"))
    return results


def run_checks(ctx, checks, progress=None):
    results = []
    for check in checks:
        regions = [ctx.home_region] if check.scope == GLOBAL else ctx.regions
        for region in regions:
            if progress:
                progress(check, _region_label(check, region))
            results.extend(run_check(ctx, check, region))
    return results


def summarise(results):
    """Counts by area and status, plus totals."""
    summary = {}
    for r in results:
        area = summary.setdefault(r.area, {s: 0 for s in STATUSES})
        area[r.status] += 1
    total = {s: sum(a[s] for a in summary.values()) for s in STATUSES}
    ordered = {a: summary[a] for a in AREAS if a in summary}
    return {"by_area": ordered, "total": total}


FAIL_ON_CHOICES = ("fail", "warn", "never")


def exit_code_for(results, fail_on):
    """0 if the run meets the threshold, 1 if not.

    fail: any FAIL. warn: any FAIL, WARN or ERROR. never: always 0.
    """
    statuses = {r.status for r in results}
    if fail_on == "fail":
        return 1 if FAIL in statuses else 0
    if fail_on == "warn":
        return 1 if statuses & {FAIL, WARN, ERROR} else 0
    return 0
