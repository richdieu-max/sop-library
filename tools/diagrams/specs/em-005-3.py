import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("From device to compliance number: the monthly report pipeline, and the expedited path",
            "Update state flows from each device into Intune and Log Analytics, becomes one KPI per ring and severity, and on day 21 raises the minimum build; a zero-day takes the expedite shortcut.",
            height=840)

# ---------------- pipeline
d.zone(32, 100, 1216, 190, "How a device's update state becomes the monthly number", icon="bar-chart", note="read-only Graph scopes for the export")
pipe = [
    ("Device", ["Entra or hybrid joined, enrolled; Allow Telemetry at Required or higher"], "laptop", C.blue),
    ("Intune reports", ["ring status Succeeded within 24 h of check-in; feature and expedite reports within 48 h"], "list-blue", C.blue),
    ("Windows data", ["connector with processor configuration on, so diagnostic data reaches the workspace"], "link", C.purple),
    ("Log Analytics", ["UCClientUpdateStatus, last 2 days, latest row per device, counted by ClientState and substate"], "chart-monitor", C.purple),
    ("KPI", ["% of devices active in the last 14 days on the release now past its SLA, per ring and severity"], "target-teal", C.teal),
]
for i, (name, body, ic, col) in enumerate(pipe):
    x = 48 + i * 240
    d.card(x, 140, 224, 102, name, body, icon=ic, accent=col, badge=str(i + 1), badge_color=col, body_size=11)
    if i < 4:
        d.arrow([(x + 224, 191), (x + 240, 191)], col)
d.text(48, 270, "Offline over 14 days: contact the owner and exclude from the KPI. Paused rings are listed in the monthly report with owner and review date.", 11, 400, C.grey, max_w=1180)

# ---------------- SLA matrix
d.zone(32, 306, 640, 232, "SLA by severity, and the pass line", icon="clock", note="agreed with vulnerability management")
d.text(48, 348, "Severity", 11.5, 600, C.ink); d.text(230, 348, "Fix within", 11.5, 600, C.ink); d.text(360, 348, "KPI target", 11.5, 600, C.ink); d.text(490, 348, "Worst case per device", 11.5, 600, C.ink)
rows = [("Actively exploited", "7 days", "≥ 98%", C.red), ("Critical", "14 days", "≥ 98%", C.red), ("High", "30 days", "≥ 95%", C.gold), ("Medium", "60 days", "≥ 95%", C.blue)]
yy = 358
for sev, sla, kpi, col in rows:
    d.text(48, yy + 17, sev, 12, 600, C.ink)
    d.status_cell(230, yy, 110, 26, sla, col)
    d.status_cell(360, yy, 110, 26, kpi, col)
    yy += 34
d.text(490, 375, "deferral + deadline + grace", 11, 400, C.grey)
d.text(490, 391, "days after release, e.g. Ring 3:", 11, 400, C.grey)
d.text(490, 407, "14 + 5 + 2 = 21 days", 11, 600, C.ink)
d.text(490, 423, "Day 21 is the compliance checkpoint", 11, 400, C.grey)
d.text(490, 439, "as every ring is past its deadline", 11, 400, C.grey)
d.text(48, 512, "Checkpoint failed? Pause every ring that has not installed yet; pauses last 35 days, then resume.", 11, 400, C.grey, max_w=600)

# ---------------- day 21 enforcement
d.zone(696, 306, 552, 232, "Day 21: compliance", icon="shield-check", note="raise the bar only after the SLA has expired")
steps21 = [("Report against the SLA", "per ring and severity, from the KPI"), ("Raise the minimum OS build", "compliance policy: the build of the release past its SLA, e.g. 10.0.26100.xxxx"),
           ("Non-compliant after grace = SLA", "devices below it fail CA006 (SOP-ID-001)"), ("Record exceptions, close the change", "only when Broad reports above 95%")]
for i, (t, b) in enumerate(steps21):
    d.card(712, 346 + i * 46, 520, 40, "", [], accent=C.green, shadow=False, badge=str(i + 1), badge_color=C.green)
    d.text(752, 362 + i * 46, t, 12, 600, C.ink)
    d.text(752, 377 + i * 46, b, 10.5, 400, C.grey, max_w=470)

# ---------------- expedite path
d.zone(32, 554, 1216, 214, "The expedited path for a zero-day", icon="lightning", fill=C.redtint, stroke=C.red, title_color=C.red, note="WU-Expedite-Template: restart enforced after 1 day (0–2)")
exp = [
    ("Day 0 review", ["release notes, release health, CVEs Exploitation Detected, CISA KEV"], C.red),
    ("Emergency change", ["record it; set the template to the release that contains the fix"], C.red),
    ("Test first", ["assign to Ring 0 Test; watch installs"], C.red),
    ("After 2–4 h of success", ["add Pilot, Broad and Validated, the last with the lab owner's approval"], C.red),
    ("Above target", ["remove the assignments once installed above target"], C.green),
]
for i, (name, body, col) in enumerate(exp):
    x = 48 + i * 240
    d.card(x, 594, 224, 84, name, body, accent=col, badge=str(i + 1), badge_color=col, shadow=False, body_size=11)
    if i < 4:
        d.arrow([(x + 224, 636), (x + 240, 636)], col)
d.callout(48, 690, 1184, 66, "Expedite shows Not applicable", kind="note",
          body=["The device is already on that build, or diagnostic data is off. Expedite, feature and driver policies also need the deployment service licence."])

d.note_bottom("SLA: exploited 7, critical 14, high 30, medium 60 days. KPI pass: ≥ 98% exploited and critical, ≥ 95% high and medium. Controls: SI-2, SI-2(2), SI-2(3), RA-5, CM-3.")
d.render(repo_path("endpoint-management/diagrams/sop-em-005-3.svg"))
