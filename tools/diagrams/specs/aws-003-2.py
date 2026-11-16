import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("From Connect to a working route: the sign-in sequence and where it fails",
            "Seven messages between the client, the browser, Identity Center and the endpoint; each failure point maps to one row of the troubleshooting table.",
            height=740, accent=C.gold, vendor="AWS")

actors = [("AWS VPN client", "app-window", C.blue), ("Browser", "globe", C.blue), ("Identity Center", "entra-user", C.purple), ("Client VPN endpoint", "lock", C.gold)]
msgs = [(0, 3, "1  Connect: endpoint asks for a SAML sign-in", C.gold, False),
        (0, 1, "2  Opens the browser to the Identity Center app", C.blue, False),
        (1, 2, "3  User signs in, MFA approved", C.purple, False),
        (2, 1, "4  SAML assertion: email + group IDs", C.purple, True),
        (1, 0, "5  POST to 127.0.0.1:35001 on the laptop", C.blue, True),
        (0, 3, "6  Assertion presented over TLS 443", C.gold, False),
        (3, 0, "7  Address from the client CIDR + routes for the group's rules", C.green, True)]
yy = d.sequence(32, 100, 1216, actors, msgs, lane_h=44)

d.zone(32, yy + 18, 1216, 150, "Where each step fails", icon="warning")
fails = [("2-3", "SAML error page", "ACS URL or audience typo; user not assigned to the app"),
         ("4", "Signed in, rejected", "memberOf mapping missing; IAM provider has old metadata"),
         ("7", "Connected, no traffic", "No rule for the group ID; resource SG does not allow sg-client-vpn")]
for i, (step, t, b) in enumerate(fails):
    d.card(48 + i * 400, yy + 58, 384, 96, f"Step {step}: {t}", [b], accent=C.red)
d.note_bottom("The browser step happens on the laptop; nothing is exposed on 35001 to the network. Controls supported: IA-2(1), IA-8, AC-17, AU-12.")
d.render(repo_path("aws-procedures/diagrams/sop-aws-003-2.svg"))
