import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Automated Device Enrollment: from Apple Business Manager to Company Portal",
            "A yearly token handshake between Intune and ABM, then a zero-touch path for every new Mac: Setup Assistant, modern sign-in, a locked MDM profile, and Company Portal as a required app.",
            height=820)

actors = [("Apple Business Manager", "apple", C.ink), ("Intune", "devices", C.blue),
          ("New Mac, Setup Assistant", "laptop", C.purple), ("User and Company Portal", "user", C.green)]
msgs = [
    (1, 0, "public key from a new enrollment program token", C.blue, False),
    (0, 0, "Your MDM Servers › Add, upload the key", C.ink, False),
    (0, 1, "server token (.p7m), uploaded with the ABM Apple Account", C.ink, True),
    (0, 0, "assign Macs: default assignment, serial or order", C.ink, False),
    (1, 1, "Sync; create the macOS profile; set as default", C.blue, False),
    (2, 0, "first power-on: is this serial assigned to an MDM server?", C.purple, False),
    (0, 2, "yes: enrollment profile applies, locked, zero-touch", C.ink, True),
    (2, 1, "modern authentication: work account and MFA", C.purple, False),
    (1, 2, "MDM profile installed: supervised, Corporate, via DEP", C.blue, True),
    (1, 1, "Await final configuration: hold", C.blue, False),
    (1, 2, "wake through APNs; the Mac checks in over HTTPS", C.blue, True),
    (1, 3, "Company Portal arrives as a Required app", C.blue, False),
    (3, 1, "user signs in: user affinity, primary user set", C.green, False),
    (1, 1, "device: ADE enrollment type, Supervised Yes", C.blue, False),
]
bottom = d.sequence(32, 100, 868, actors, msgs, lane_h=34)

# phase brackets on the far left of the sequence
d.pill(820, 158, "once a year", C.ink)
d.pill(820, 338, "every new Mac", C.purple)
d.line(40, 168, 40, 330, C.ink, 2); d.line(40, 340, 40, 652, C.purple, 2)

# ---------------- right column
d.zone(924, 100, 324, 196, "Profile settings for zero-touch", icon="checklist-purple")
d.card(938, 140, 296, 44, "Enroll with User Affinity", ["assigned Macs; none for shared Macs"], accent=C.purple, shadow=False, title_size=12.5, body_size=11)
d.card(938, 190, 296, 44, "Modern authentication at setup", ["work account and MFA in Setup Assistant"], accent=C.purple, shadow=False, title_size=12.5, body_size=11)
d.card(938, 240, 296, 44, "Locked enrollment: Yes", ["removable only by Intune or an erase"], accent=C.purple, shadow=False, title_size=12.5, body_size=11)

d.zone(924, 312, 324, 178, "Verify on the Mac and in Intune", icon="check-circle")
d.text(938, 358, "sudo profiles status -type enrollment", 11, 600, C.ink, mono=True)
d.text(938, 376, "MDM enrollment: Yes (User Approved)", 11, 400, C.grey, mono=True)
d.text(938, 392, "Enrolled via DEP: Yes", 11, 400, C.grey, mono=True)
d.line(938, 404, 1234, 404, C.rule)
d.lines(938, 424, "Intune device properties: Enrollment type Apple automated device enrollment, Supervised: Yes, correct primary user and a recent check-in.", 11.5, 296)

d.callout(924, 506, 324, 150, "If the Mac skips enrollment", kind="warn",
          body=["Not assigned to the MDM server, token not synced, or no profile. Assign, sync, then erase the Mac or run sudo profiles renew -type enrollment.", "Moving an existing Mac to ADE means erasing it."])

# ---------------- bottom strip
d.callout(32, 672, 868, 84, "Token and account hygiene", kind="note", icon="calendar",
          body=["The ABM token expires after one year and a token error also follows changed ABM terms: renew in ABM, upload, sync. The APNs certificate is renewed, never re-created, or every Apple device must re-enroll."])
d.callout(924, 672, 324, 84, "Network", kind="info", icon="wifi",
          body=["Macs reach *.push.apple.com (TCP 443/5223) and *.manage.microsoft.com with no TLS inspection."])

d.note_bottom("14 steps: 5 once a year, 9 per Mac. Result: supervised, locked, always Corporate. Controls: CM-8 (inventory with owner and ownership type), CM-3 (restrictions under change control).")
d.render(repo_path("endpoint-management/diagrams/sop-em-002-2.svg"))
