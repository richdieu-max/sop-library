import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Register, install, connect, verify: the agent's path to a healthy connection",
            "Every method starts in the console and ends with the same proof: the workstation listed under its System, a current last-contact time, and a test event captured and signed.",
            height=740)

actors = [("Administrator", "user", C.blue), ("Web console (HTTPS)", "app-window", C.purple),
          ("Workstation agent service", "monitor", C.green), ("Compliance server", "server", C.gold)]
msgs = [
    (0, 1, "Workstations › Add: exact hostname, System, lab, owner, purpose", C.blue, False),
    (1, 1, "System Reload if needed; screenshot the entry", C.purple, False),
    (0, 2, "Test-AgentPrereqs.ps1: admin rights, time source, DNS, port, disk, pending reboot", C.blue, False),
    (0, 2, "copy the MSI locally, check SHA-256 against the repository, msiexec /i elevated", C.blue, False),
    (0, 2, "Connections: server, port, authentication; service Automatic; restart", C.blue, False),
    (2, 3, "connect over TLS on <agent-port>; hostname checked", C.green, False),
    (3, 2, "accepted: capture rules for the System", C.gold, True),
    (3, 1, "workstation listed under its System; last contact current", C.gold, True),
    (2, 2, "test file in a monitored folder: event captured", C.green, False),
    (2, 3, "event uploaded with who and when; signed with a test account", C.green, False),
]
bottom = d.sequence(32, 100, 864, actors, msgs, lane_h=37)

# ---- right column: where it goes wrong
d.zone(920, 100, 328, 330, "Where it goes wrong", icon="warning", fill=C.redtint, stroke=C.red, title_color=C.red)
d.card_col(934, 140, 300, 62, [
    {"title": "Installed but never connects", "body": ["no connection entry: add it, save, restart the service"], "accent": C.red},
    {"title": "Entry exists, still red", "body": ["not registered, or the server was not reloaded"], "accent": C.red},
    {"title": "TcpTestSucceeded : False", "body": ["firewall or VLAN ACL: request source, destination and port"], "accent": C.red},
    {"title": "Starts then stops (7034 / 7031)", "body": ["service account password or Log on as a service"], "accent": C.red},
], gap=8, shadow=False, title_size=12.5, body_size=11)

d.callout(920, 446, 328, 100, "Hostname mismatch is the usual cause", kind="note", icon="id-card",
          body=["A typo, the old name after a reimage, or NetBIOS differing from DNS: the console entry must match what hostname reports."])
d.callout(920, 562, 328, 84, "Still disconnected?", kind="info", icon="refresh-green",
          body=["With correct configuration, one clean reboot, recorded, often fixes it."])

# ---- bottom: the data-integrity rule
d.callout(32, bottom + 14, 864, 84, "Never delete the agent's local queue or database to clear an error", kind="warn", icon="db-blue",
          body=["It destroys unsent audit-trail events, which is a data-integrity incident. Work outward instead: service running, connection entry present, port reachable, then registration; reinstalling is the last resort."])

d.note_bottom("Time must be domain-synchronized (w32tm /query /status) before any of this: audit-trail timestamps depend on it. Controls: 21 CFR Part 11 §11.10(e) audit trails; ALCOA+ Attributable and Contemporaneous.")
d.render(repo_path("regulated-lab-it/diagrams/sop-lab-002-2.svg"))
