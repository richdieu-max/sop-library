import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("The logging pipeline: sources, the working window and the locked record",
            "Every source streams to one workspace that the alerts read; data export copies the same rows to a WORM archive nobody can shorten, whose lock is the data owner's decision alone.",
            height=780)

# ---- sources
d.zone(32, 100, 300, 400, "Sources", icon="list-blue", note="each has a diagnostic setting")
src = [("Subscription activity log", "diagnostic setting: Administrative, Security, Policy, Alert, ServiceHealth", "cloud", C.blue),
       ("Root group activity log", "diagnostic setting set by API only; policy and role changes at the root live here, never in the subscription export", "hierarchy", C.purple),
       ("Key Vault, storage, vaults", "resource diagnostic settings (audit categories)", "lock", C.gold),
       ("VM syslog and performance", "Azure Monitor Agent with a data collection rule", "vm-cluster", C.teal)]
for i, (t, b, ic, col) in enumerate(src):
    d.card(46, 140 + i * 84, 272, 76, t, [b], icon=ic, accent=col, shadow=False, title_size=12, body_size=10.5)
    d.line(318, 178 + i * 84, 352, 178 + i * 84, C.grey, 1.5)
d.line(352, 178, 352, 430, C.grey, 1.5)
d.arrow([(352, 292), (382, 292)], C.grey, sw=1.5)

# ---- workspace
d.zone(384, 100, 300, 400, "Log Analytics workspace", icon="bar-chart")
d.card(398, 140, 272, 96, "Searchable retention", ["interactive and total retention recorded from Settings › Tables; the build sets 365 days. KQL query 1 lists which tables actually received rows in the last day"], accent=C.blue, shadow=False, title_size=12, body_size=10.5)
d.card(398, 244, 272, 118, "What reads it", ["activity-log alert rules, one per destructive or privileged operation; scheduled-query rules for guardrail changes (severity 1, every 15 minutes) and the workload; the matching queries for the test"], icon="bell", accent=C.red, shadow=False, title_size=12, body_size=10.5)
d.card(398, 370, 272, 100, "Who, what, when", ["AzureActivity rows carry Caller, CallerIpAddress, OperationNameValue, the resource and a CorrelationId, time-stamped by the platform in UTC"], icon="doc-check-green", accent=C.green, shadow=False, title_size=12, body_size=10.5)
d.arrow([(670, 292), (704, 292), (704, 292), (734, 292)], C.grey, label="data export", sw=1.5, label_dy=-8)

# ---- archive
d.zone(736, 100, 512, 400, "WORM archive", icon="hash-doc", note="the regulatory record")
d.card(750, 140, 484, 90, "Geo-redundant storage account", ["minimum TLS 1.2, public blob access off, public network access off; am-* containers each under a time-based retention policy of 7 years with protected append writes allowed"], icon="server", accent=C.purple, shadow=False, title_size=12, body_size=10.5)
d.text(750, 262, "Lock state of the retention policy", 12, 600, C.ink)
d.card(750, 272, 232, 100, "Unlocked (as built)", ["policy can still be changed; the data inside it still cannot be deleted before the retention ends; this is the state recorded at validation"], accent=C.gold, shadow=False, title_size=12, body_size=10.5, pill=("recorded", C.gold))
d.card(1000, 272, 234, 100, "Locked", ["permanent and irreversible; done only by the data owner, never by the engineer, with the Lock script handed over for that moment"], accent=C.red, shadow=False, title_size=12, body_size=10.5, pill=("owner only", C.red))
d.arrow([(982, 322), (1000, 322)], C.red, sw=1.5)
d.callout(750, 386, 484, 100, "Never shortened, never deleted", kind="warn", body=["Rollback removes everything else in reverse order but never the archive storage account: an unlocked WORM policy still blocks deleting the data inside it until the retention ends."])

# ---- bottom: what validation records
d.zone(32, 520, 1216, 176, "What the validation run records", icon="checklist-purple")
cols = [("Source inventory", "every resource, the subscription and the root group have a setting pointing at the workspace; query 1 shows rows arriving", C.blue),
        ("Retention", "workspace interactive and total retention; each archive container's retention period and lock state", C.purple),
        ("Alert rules", "the list from Monitor › Alerts › Alert rules, each fired once in the test window and matched to its log row", C.red),
        ("Time source", "every time in UTC from the platform, not a laptop clock: contemporaneous under ALCOA+ and 21 CFR Part 11", C.green)]
for i, (t, b, col) in enumerate(cols):
    d.card(46 + i * 300, 560, 288, 122, t, [b], accent=col, badge=str(i + 1), badge_color=col, shadow=False, title_size=12.5, body_size=11)

d.note_bottom("Working window 365 days; archive retention 7 years (2,557 days) time-based WORM, geo-redundant. Controls: AU-2, AU-3, AU-8, AU-9, AU-11; ISO A.8.15, A.8.17; 21 CFR Part 11 §11.10(e).")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-107-2.svg"))
