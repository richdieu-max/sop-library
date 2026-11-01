import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("The coexistence window and the verify-clean checklist",
            "Never two real-time engines, never an unprotected machine: model A lets Defender Antivirus cover a timed gap, model B overlaps Defender for Endpoint in passive mode so there is no gap.",
            height=840)

# ---------------- timelines
d.zone(32, 100, 1216, 300, "One endpoint, two sequencing models", icon="clock", note="drivers unload only at restart; an unload password is not removal")
x0, x1 = 300, 1232
def seg(y, a, b, color, label, sub=None, text_color="#fff"):
    d.parts.append(f'<rect x="{x0 + (x1 - x0) * a:.0f}" y="{y}" width="{(x1 - x0) * (b - a):.0f}" height="30" rx="4" fill="{color}"/>')
    d.text(x0 + (x1 - x0) * (a + b) / 2, y + 15 if sub else y + 19, label, 11.5, 600, text_color, "middle")
    if sub:
        d.text(x0 + (x1 - x0) * (a + b) / 2, y + 26, sub, 10, 400, text_color, "middle")
def marker(y, pos, label, color=C.ink):
    px = x0 + (x1 - x0) * pos
    d.line(px, y - 6, px, y + 36, color, 1.5, dashed=True)
    d.text(px, y - 10, label, 10.5, 600, color, "middle")

# Model A
d.card(48, 146, 236, 92, "Remove, then install", ["third-party EDR that needs a clean machine, e.g. CylancePROTECT"], badge="A", accent=C.red, shadow=False, body_size=11)
yA = 160
seg(yA, 0.00, 0.30, C.red, "legacy AV active", "real-time engine, minifilter loaded")
seg(yA, 0.30, 0.62, C.gold, "gap: Defender Antivirus covers", "AMRunningMode Normal, real-time on")
seg(yA, 0.62, 1.00, C.green, "new EDR active", "healthy, in Security Center, EICAR detected")
marker(yA, 0.30, "uninstall or SCUT, reboot", C.red)
marker(yA, 0.46, "verify clean", C.gold)
marker(yA, 0.54, "certificates", C.gold)
marker(yA, 0.62, "install EDR", C.green)
d.text(x0 + (x1 - x0) * 0.46, yA + 50, "record the time between removal and confirmed protection in the change record", 10.5, 400, C.grey, "middle")

# Model B
d.card(48, 268, 236, 110, "Overlap, then remove", ["migrating to Defender for Endpoint per Microsoft's guidance; no gap"], badge="B", accent=C.blue, shadow=False, body_size=11)
yB = 262
seg(yB, 0.00, 0.50, C.red, "legacy AV active", "still the registered engine")
seg(yB + 36, 0.12, 0.50, C.blue, "Defender for Endpoint in passive mode", "onboarded, mutual exclusions set")
seg(yB + 36, 0.50, 1.00, C.green, "Defender for Endpoint active", "takes over as the legacy AV leaves Security Center")
marker(yB, 0.12, "onboard MDE (passive)", C.blue)
marker(yB, 0.50, "remove legacy AV, reboot", C.red)
d.text(x0 + (x1 - x0) * 0.75, yB + 90, "no window without a real-time engine", 10.5, 600, C.green, "middle")

# ---------------- why never two engines
d.callout(32, 416, 600, 96, "Why two real-time engines must never overlap", kind="warn",
          body=["Each one inserts a file-system minifilter into the Windows I/O path and intercepts every file operation: double scanning, deadlocks, each quarantining the other, blue screens."])
d.zone(656, 416, 592, 96, "Defender Antivirus steps aside, then steps back", icon="defender-shield")
d.lines(672, 456, "It goes passive when another AV registers with Windows Security Center and turns itself back on when that AV is removed, which is what covers the model A gap. Rollback: if the new EDR cannot be installed, keep Defender as a documented interim control or reinstall the legacy agent; record which state the endpoint is in.", 11, 560, 400, C.grey, lh=15)

# ---------------- verify clean checklist
d.zone(32, 528, 1216, 232, "Prove it is gone: every check must pass before the EDR is installed", icon="check-circle", note="Test-LegacyAVRemoved.ps1, elevated, after the reboot")
checks = [
    ("Services", "no Tm*, ntrtscan, TMBMServer", "gear"),
    ("Processes", "no PccNTMon, Tm*, NTRtScan", "app-window"),
    ("Drivers", "fltmc filters shows no tm* minifilter", "chip"),
    ("Registry", "no HKLM\\SOFTWARE\\TrendMicro, nor WOW6432Node", "list-blue"),
    ("Programs and folders", "no entry; program folder gone (empty log-only folder: record it)", "folder"),
    ("Security Center", "root/SecurityCenter2 no longer lists the legacy AV", "shield-check"),
    ("During the gap", "Get-MpComputerStatus: AMRunningMode Normal, real-time on", "defender-shield"),
    ("New EDR", "healthy locally, online in its console, in Security Center, EICAR detected", "check-circle"),
]
for i, (t, b, ic) in enumerate(checks):
    x = 48 + (i % 4) * 300
    y = 568 + (i // 4) * 80
    d.card(x, y, 284, 70, t, [b], icon=ic, badge=str(i + 1), badge_color=C.green, accent=C.green, shadow=False, title_size=12.5, body_size=10.5)
d.chips(48, 732, [("exit 0 · clean", C.green), ("exit 3010 · clean after reboot", C.gold), ("exit 1 · failed", C.red)])
d.text(436, 747, "Remove-LegacyAV.ps1 exit codes. Services still active after a reboot: the self-protection driver is loaded, run the tool from Safe Mode.", 10.5, 400, C.grey, max_w=800)

d.note_bottom("Pilot 5–20 endpoints across hardware models first; uninstall password vaulted, logged per use and rotated. Controls: SI-3 (never without an engine), CM-3, AC-6, IA-5, AU-12 (transcripts, JSON footprints, SCUT -dbg logs).")
d.render(repo_path("endpoint-agents/diagrams/sop-ep-002-3.svg"))
