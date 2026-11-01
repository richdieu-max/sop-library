import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Four ways to install the same agent, and the hotfix path with its rollback",
            "Pick the method by how many PCs and whether hands are on the keyboard; the hotfix is its own controlled change, tested first and reversible.",
            height=800)

# ---------------- methods A–D
d.zone(32, 100, 1216, 310, "Methods A–D side by side", icon="checklist-purple", note="letters are alternatives; every method starts with console registration")
cards = [
    {"title": "Interactive", "badge": "A", "accent": C.blue, "pill": ("1–3 PCs, hands on", C.blue), "icon": "laptop",
     "body": ["How: MSI copied locally, SHA-256 checked, msiexec /i from an elevated prompt; connection added in the Agent Configuration Utility; service Automatic, restarted",
              "Evidence: screenshots of Connections and the console",
              "Pitfall: correct config but still disconnected: one clean reboot, recorded"]},
    {"title": "Silent", "badge": "B", "accent": C.purple, "pill": ("scripted batches", C.purple), "icon": "terminal",
     "body": ["How: Install-ComplianceAgent.ps1 checks the checksum, installs /qn with a verbose log, sets service identity, Automatic start and restart-on-failure; -WhatIf first",
              "Evidence: msiexec log and a JSON evidence file",
              "Pitfall: exit 0 or 3010 only; MSI property names are product-specific (Orca)"]},
    {"title": "Remote", "badge": "C", "accent": C.green, "pill": ("1–3 PCs, remote", C.green), "icon": "link",
     "body": ["How: BeyondTrust PRA Jump Item (File Transfer, then Screen Sharing or Command Shell) or PowerShell remoting with Copy-Item -ToSession; never during acquisition",
              "Evidence: the session recording",
              "Pitfall: a UNC path inside the session fails on the Kerberos double hop"]},
    {"title": "Enterprise", "badge": "D", "accent": C.gold, "pill": ("fleets", C.gold), "icon": "devices",
     "body": ["How: ConfigMgr application (product-code detection, maintenance window, supersedence) or Intune Win32 app (detection by product code, scope tag, no maintenance window)",
              "Evidence: deployment success list",
              "Pitfall: Intune has no maintenance window: deadline time, or keep validated PCs on ConfigMgr"]},
]
d.card_row(48, 146, 284, 214, cards, gap=16, body_size=11.5)
d.text(48, 392, "Remote sessions usually run the Method B commands; whichever route you take, the Verify table is the same.", 11.5, 400, C.grey)

# ---------------- hotfix path
d.zone(32, 426, 1216, 176, "Hotfix: from release notes to a signed test event", icon="package", note="one controlled change, tested on a test system first")
steps = [
    ("Assess with Quality", "data capture, signatures, audit trail touched? server and agent versions must match? OQ scripts cover it?"),
    ("Test, then approve", "pass on a test system; change approved; window booked with the lab"),
    ("Pre-checks", "package checksum; agent queue empty; console last contact current"),
    ("Apply", "stop the service if the vendor requires; msiexec /p for an .msp; start the service"),
    ("Confirm", "Connections healthy, console visible, new version shown"),
    ("Prove it", "create a file in a monitored folder; watch the event arrive; sign it with a test account"),
]
for i, (t, b) in enumerate(steps):
    x = 48 + i * 196
    d.card(x, 468, 186, 118, t, [b], badge=str(i + 1), accent=C.gold, shadow=False, title_size=12.5, body_size=10.5)
    if i < 5:
        d.arrow([(x + 186, 527), (x + 196, 527)], C.gold, sw=1.6)

# ---------------- rollback
d.zone(32, 618, 1216, 112, "Rollback, if verification fails", icon="refresh-green", fill=C.redtint, stroke=C.red, title_color=C.red)
rb = [
    ("Stop the service", "inside the agreed window"),
    ("Remove the hotfix", "msiexec MSIPATCHREMOVE for an uninstallable .msp"),
    ("Known-good version", "msiexec /x, reboot, install the approved build"),
    ("Re-add the connection", "Agent Configuration Utility › Connections"),
    ("Validate and record", "reason logged; problem record if the vendor must investigate"),
]
for i, (t, b) in enumerate(rb):
    x = 48 + i * 236
    d.card(x, 658, 224, 62, t, [b] if b else [], accent=C.red, shadow=False, title_size=12.5, body_size=10.5)
    if i < 4:
        d.arrow([(x + 224, 689), (x + 236, 689)], C.red, sw=1.6)

d.note_bottom("Exit 0 = success, 3010 = success with reboot; msiexec 1603: search the verbose log for 'Return value 3'. Controls: 21 CFR Part 11 §11.10(a); EU GMP Annex 11 §10 change and configuration management.")
d.render(repo_path("regulated-lab-it/diagrams/sop-lab-002-3.svg"))
