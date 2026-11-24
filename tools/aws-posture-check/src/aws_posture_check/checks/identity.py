"""Identity: the root user, IAM users and IAM Identity Center (account-wide checks)."""

import csv
import io

from ..core import (
    ERROR, FAIL, GLOBAL, PASS, WARN, days_between, error_code, outcome, paginate,
    parse_time, register,
)

AREA = "Identity"
ROOT_ROW = "<root_account>"
ROOT_RECENT_USE_DAYS = 30
KEY_MAX_AGE_DAYS = 90
KEY_UNUSED_DAYS = 45
MIN_PASSWORD_LENGTH = 14
MIN_PASSWORD_REUSE = 24


def account_summary(ctx):
    return ctx.cached("iam:summary", lambda: ctx.client("iam").get_account_summary().get("SummaryMap", {}))


def credential_report(ctx, attempts=10, delay=2):
    """The IAM credential report as a list of dicts (generated if needed, then cached)."""

    def load():
        iam = ctx.client("iam")
        for _ in range(attempts):
            if iam.generate_credential_report().get("State") == "COMPLETE":
                break
            ctx.sleep(delay)
        content = iam.get_credential_report().get("Content", b"")
        if isinstance(content, bytes):
            content = content.decode("utf-8")
        return list(csv.DictReader(io.StringIO(content)))

    return ctx.cached("iam:credential_report", load)


def _true(value):
    return str(value).strip().lower() == "true"


@register(
    "IAM-01", AREA, "Root user has MFA enabled", GLOBAL,
    nist=("IA-2(1)", "AC-6(5)"), cis="1.5",
    remediation="Sign in as root, Security credentials, Assign MFA device; register two FIDO2 security keys (SOP-AWS-001 step 2).",
)
def root_mfa(ctx, region):
    enabled = account_summary(ctx).get("AccountMFAEnabled") == 1
    if enabled:
        yield outcome(PASS, "root", "Root user MFA is enabled")
    else:
        yield outcome(FAIL, "root", "Root user has no MFA device")


@register(
    "IAM-02", AREA, "Root user MFA is a security key, not a virtual device", GLOBAL,
    nist=("IA-2(1)", "IA-5"), cis="1.6",
    remediation="Replace the root virtual MFA device with two FIDO2 security keys stored apart.",
)
def root_hardware_mfa(ctx, region):
    if account_summary(ctx).get("AccountMFAEnabled") != 1:
        yield outcome(FAIL, "root", "Root user has no MFA device (see IAM-01)")
        return
    virtual = [
        d for d in paginate(ctx.client("iam"), "list_virtual_mfa_devices", "VirtualMFADevices",
                            AssignmentStatus="Assigned")
        if str((d.get("User") or {}).get("Arn", "")).endswith(":root")
        or str(d.get("SerialNumber", "")).endswith("/root-account-mfa-device")
    ]
    if virtual:
        yield outcome(WARN, "root", "Root user MFA includes a virtual (authenticator app) device: %s"
                      % ", ".join(d.get("SerialNumber", "?") for d in virtual))
    else:
        yield outcome(PASS, "root", "Root user MFA uses security keys or hardware devices only")


@register(
    "IAM-03", AREA, "Root user has no access keys", GLOBAL,
    nist=("AC-6(5)", "IA-5"), cis="1.4",
    remediation="Delete every root access key (Security credentials, Access keys). Never create one for root.",
)
def root_access_keys(ctx, region):
    present = account_summary(ctx).get("AccountAccessKeysPresent", 0)
    if present:
        yield outcome(FAIL, "root", "Root user has %s access key(s)" % present)
    else:
        yield outcome(PASS, "root", "Root user has no access keys")


@register(
    "IAM-04", AREA, "Root user not used in the last %d days" % ROOT_RECENT_USE_DAYS, GLOBAL,
    nist=("AC-6(5)", "AC-2"), cis="1.7",
    remediation="Stop using root day to day: use IAM Identity Center permission sets and keep root credentials under dual control.",
)
def root_recent_use(ctx, region):
    rows = [r for r in credential_report(ctx) if r.get("user") == ROOT_ROW]
    if not rows:
        yield outcome(ERROR, "root", "Root user row missing from the credential report")
        return
    row = rows[0]
    used = [parse_time(row.get(k)) for k in
            ("password_last_used", "access_key_1_last_used_date", "access_key_2_last_used_date")]
    used = [u for u in used if u]
    if not used:
        yield outcome(PASS, "root", "No recorded root sign-in or key use")
        return
    last = max(used)
    age = days_between(last, ctx.now)
    detail = "Root user last used %s (%d days ago)" % (last.strftime("%Y-%m-%d"), age)
    yield outcome(WARN if age < ROOT_RECENT_USE_DAYS else PASS, "root", detail)


def _console_users(ctx):
    return [r for r in credential_report(ctx)
            if r.get("user") != ROOT_ROW and _true(r.get("password_enabled"))]


@register(
    "IAM-05", AREA, "IAM password policy: length %d or more, reuse prevention %d"
    % (MIN_PASSWORD_LENGTH, MIN_PASSWORD_REUSE), GLOBAL,
    nist=("IA-5(1)",), cis="1.8, 1.9",
    remediation="aws iam update-account-password-policy --minimum-password-length 14 --password-reuse-prevention 24 "
                "--require-symbols --require-numbers --require-uppercase-characters --require-lowercase-characters",
)
def password_policy(ctx, region):
    try:
        policy = ctx.client("iam").get_account_password_policy().get("PasswordPolicy", {})
    except Exception as exc:
        if error_code(exc) != "NoSuchEntity":
            raise
        try:
            users = len(_console_users(ctx))
        except Exception:
            users = None
        if users:
            yield outcome(FAIL, "password-policy",
                          "No account password policy, and %d IAM user(s) have a console password" % users)
        else:
            yield outcome(WARN, "password-policy",
                          "No account password policy is set (no IAM users with a console password were found)")
        return
    gaps = []
    if policy.get("MinimumPasswordLength", 0) < MIN_PASSWORD_LENGTH:
        gaps.append("minimum length %s (needs %d)" % (policy.get("MinimumPasswordLength"), MIN_PASSWORD_LENGTH))
    if policy.get("PasswordReusePrevention", 0) < MIN_PASSWORD_REUSE:
        gaps.append("reuse prevention %s (needs %d)" % (policy.get("PasswordReusePrevention", 0), MIN_PASSWORD_REUSE))
    if gaps:
        yield outcome(FAIL, "password-policy", "Password policy is weaker than required: " + "; ".join(gaps))
    else:
        yield outcome(PASS, "password-policy", "Minimum length %s, reuse prevention %s"
                      % (policy.get("MinimumPasswordLength"), policy.get("PasswordReusePrevention")))


@register(
    "IAM-06", AREA, "IAM Identity Center is in use for people", GLOBAL,
    nist=("AC-2", "IA-2"), cis="1.21",
    remediation="Enable IAM Identity Center in the home region and give people permission sets instead of IAM users "
                "(SOP-AWS-001 steps 6 to 9). If it is enabled in another region, rerun with --home-region.",
)
def identity_center(ctx, region):
    instances = list(paginate(ctx.client("sso-admin", region), "list_instances", "Instances"))
    active = [i for i in instances if i.get("Status", "ACTIVE") == "ACTIVE"]
    if active:
        yield outcome(PASS, active[0].get("InstanceArn", "identity-center"),
                      "IAM Identity Center instance found in %s" % region, region=region)
    else:
        yield outcome(WARN, "identity-center",
                      "No active IAM Identity Center instance in %s (the home region)" % region, region=region)


@register(
    "IAM-07", AREA, "IAM users with a console password have MFA", GLOBAL,
    nist=("IA-2(1)", "IA-2(2)"), cis="1.10",
    remediation="Assign an MFA device to the user, or remove the console password and move the person to IAM Identity Center.",
)
def console_users_mfa(ctx, region):
    users = _console_users(ctx)
    if not users:
        yield outcome(PASS, "iam-users", "No IAM users have a console password")
        return
    for row in users:
        if _true(row.get("mfa_active")):
            yield outcome(PASS, row.get("arn") or row.get("user"), "Console password with MFA")
        else:
            yield outcome(FAIL, row.get("arn") or row.get("user"), "Console password without MFA")


@register(
    "IAM-08", AREA, "Active IAM access keys are rotated (%d days) and in use (%d days)"
    % (KEY_MAX_AGE_DAYS, KEY_UNUSED_DAYS), GLOBAL,
    nist=("IA-5(1)", "AC-2(3)"), cis="1.12, 1.14",
    remediation="Rotate the key (create, deploy, deactivate, delete), or delete it if unused. Prefer roles and "
                "Identity Center short-term credentials over IAM user keys.",
)
def access_key_age(ctx, region):
    found = False
    for row in credential_report(ctx):
        if row.get("user") == ROOT_ROW:
            continue
        for n in ("1", "2"):
            if not _true(row.get("access_key_%s_active" % n)):
                continue
            found = True
            resource = "%s (key %s)" % (row.get("arn") or row.get("user"), n)
            rotated = parse_time(row.get("access_key_%s_last_rotated" % n))
            last_used = parse_time(row.get("access_key_%s_last_used_date" % n))
            age = days_between(rotated, ctx.now) if rotated else None
            if age is not None and age > KEY_MAX_AGE_DAYS:
                yield outcome(FAIL, resource, "Active key is %d days old" % age)
                continue
            idle = days_between(last_used or rotated, ctx.now) if (last_used or rotated) else None
            if idle is not None and idle > KEY_UNUSED_DAYS:
                yield outcome(WARN, resource, "Active key not used for %d days" % idle
                              if last_used else "Active key never used, created %d days ago" % idle)
                continue
            yield outcome(PASS, resource, "Active key is %s days old" % (age if age is not None else "?"))
    if not found:
        yield outcome(PASS, "iam-users", "No active IAM user access keys")
