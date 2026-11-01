import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Client registration: from install to a healthy peer",
            "The installer reads tanium-init.dat beside it, the service registers on TCP 17472 with the server's trust key, joins the subnet peer chain, and the console can ask it questions.",
            height=840)

actors = [("Installer + tanium-init.dat", "package", C.grey), ("Tanium Client service", "gear-box", C.blue),
          ("Tanium Server or Zone Server", "server", C.purple), ("Console (HTTPS 443)", "app-window", C.teal)]
msgs = [
    (0, 0, "both files staged together; SHA-256 checked", C.grey, False),
    (0, 1, "SetupClient.exe /S reads the init file from its own folder", C.grey, False),
    (1, 1, "service starts; set to Automatic", C.blue, False),
    (1, 2, "register on TCP 17472: server name list, port, trust key", C.blue, False),
    (2, 1, "registered; questions and packages follow", C.purple, True),
    (1, 1, "peer chain with subnet neighbours on 17472", C.blue, False),
    (2, 1, "only the leader and backward leader talk to the server", C.purple, True),
    (3, 2, "Interact question filtered to the host", C.teal, False),
    (2, 1, "question passed along the chain", C.purple, False),
    (1, 2, "answer returned", C.blue, True),
    (2, 3, "Client Management: Online, version, computer groups", C.purple, True),
    (1, 1, "JSON evidence written with the change reference", C.blue, False),
]
bottom = d.sequence(32, 100, 880, actors, msgs, lane_h=34)

# ---------------- right panel: installed but invisible
d.zone(936, 100, 312, 350, "Installed but invisible", icon="shield-x", fill=C.redtint, stroke=C.red, dashed=True, title_color=C.red)
fails = [
    ("No init file beside the installer", "install succeeds, service runs, never registers"),
    ("Init file from another environment", "wrong server list or trust key: reinstall with the right file"),
    ("17472 blocked", "TcpTestSucceeded False: ask for a firewall or routing rule"),
    ("Clock skew", "key or certificate errors in log0.txt: w32tm /resync, reinstall"),
    ("Cloned after install", "two endpoints share one identity: reset the clone"),
]
yy = 140
for t, b in fails:
    d.card(952, yy, 280, 56, t, [b], accent=C.red, shadow=False, title_size=12, body_size=10.5)
    yy += 60

# ---------------- right panel: ports
d.zone(936, 466, 312, 150, "Ports that matter", icon="ports-blue")
ports = [("TCP 17472", "client → server or Zone Server: registration, questions, packages", C.blue),
         ("TCP 17472", "client ↔ client on the same subnet: peer chaining", C.blue),
         ("TCP 443", "operator browser → server: the console", C.teal)]
yy = 504
for p, what, col in ports:
    d.pill(952, yy, p, col, solid=True)
    d.lines(1040, yy + 13, what, 10.5, 196, 400, C.grey, lh=14)
    yy += 36

# ---------------- bottom: verify ladder
vz = 630
d.zone(32, vz, 1216, 150, "Proof the client is healthy, in the order to check it", icon="check-circle", note="service, then init file, then 17472, then the log")
checks = [("Get-Service 'Tanium Client'", "Running, Automatic"), ("Get-NetTCPConnection -RemotePort 17472", "Established connection to the server"),
          ("log0.txt in the install folder", "registration lines, no repeated errors"), ("TaniumClient.exe config get ServerNameList", "the expected server"),
          ("Interact question filtered to the host", "answer returned"), ("Client Management health view", "Online, expected version, expected computer groups")]
for i, (cmd, pas) in enumerate(checks):
    x = 48 + (i % 3) * 400
    y = vz + 40 + (i // 3) * 52
    d.card(x, y, 384, 46, "", [], accent=C.green, shadow=False, badge=str(i + 1), badge_color=C.green)
    d.text(x + 42, y + 19, cmd, 11, 600, C.ink, max_w=330)
    d.text(x + 42, y + 35, pas, 10.5, 400, C.grey, max_w=330)

d.note_bottom("Only the chain leader and backward leader reach the server; a host firewall that blocks peering makes every client talk to the server directly. Controls: CM-8, SI-7 (hashes and trust key), AU-12 (JSON evidence).")
d.render(repo_path("endpoint-agents/diagrams/sop-ep-001-2.svg"))
