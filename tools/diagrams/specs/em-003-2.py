import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Where two-person control stops: the bypass map and the compensating controls",
            "Four ways a device gets erased; only one of them passes through the Multi Admin Approval gate, so each of the others needs its own control.",
            height=760)

# ---------------- column 1: who can trigger
d.zone(32, 100, 352, 470, "Who can trigger wipe, retire or delete", icon="users")
d.card(48, 140, 320, 92, "Admin in the admin center", ["or calling Graph with delegated permissions: a person is behind the call"],
       badge="A", badge_color=C.green, accent=C.green, pill=("gated", C.green))
d.card(48, 248, 320, 92, "Application-permission app", ["an app registration with Intune Graph permissions: no user behind the call, so MAA never sees it"],
       badge="B", badge_color=C.red, accent=C.red, pill=("open", C.red))
d.card(48, 356, 320, 92, "Retire or delete", ["wipe, retire and delete are separate policy types; a wipe policy alone leaves the other two open"],
       badge="C", badge_color=C.gold, accent=C.gold, pill=("per policy", C.gold))
d.card(48, 464, 320, 92, "Holding the device", ["a factory reset on the Mac or PC itself never touches Intune"],
       badge="D", badge_color=C.grey, accent=C.grey, pill=("no Intune", C.grey))

# ---------------- column 2: the gate
d.zone(416, 100, 420, 240, "Multi Admin Approval gate", icon="policy-shield", fill="#fff", stroke=C.green, note="initiator ≠ approver")
d.card(432, 142, 120, 92, "Request", ["justification added by the initiator"], badge="1", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.arrow([(552, 182), (566, 182)], C.green, sw=1.6)
d.card(568, 142, 120, 92, "Approve", ["a different admin; notes recorded"], badge="2", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.arrow([(688, 182), (702, 182)], C.green, sw=1.6)
d.card(704, 142, 118, 92, "Complete", ["initiator; the action runs only now"], badge="3", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.lines(432, 262, "Nobody approves their own request, Global Administrators included. Approvers must be members (not owners) of a Security group that holds an Intune role with device-action Read.", 11.5, 388)

# the device at the right of column 2
d.card(626, 376, 196, 92, "The device", ["wiped, retired or deleted"], icon="phone-x", accent=C.ink)

# bypass lanes
d.zone(416, 348, 196, 224, "Bypass lanes", icon="shield-x", fill=C.redtint, stroke=C.red, dashed=True, title_color=C.red)
d.text(432, 396, "B · application permission", 11.5, 600, C.red)
d.text(432, 412, "straight to the action", 11, 400, C.grey)
d.text(432, 448, "C · policy not created", 11.5, 600, C.gold)
d.text(432, 464, "retire/delete run ungated", 11, 400, C.grey)
d.text(432, 500, "D · factory reset", 11.5, 600, C.grey)
d.text(432, 516, "never reaches Intune", 11, 400, C.grey)

# arrows from sources
d.arrow([(368, 186), (400, 186), (400, 182), (432, 182)], C.green, sw=2)                  # A into gate
d.arrow([(822, 182), (860, 182), (860, 300), (724, 300), (724, 376)], C.green, sw=2)      # gate to device
d.arrow([(368, 294), (400, 294), (400, 404), (432, 404)], C.red, dashed=True, sw=1.8)    # B into bypass
d.arrow([(368, 402), (400, 402), (400, 456), (432, 456)], C.gold, dashed=True, sw=1.8)   # C into bypass
d.arrow([(368, 510), (432, 510)], C.grey, dashed=True, sw=1.8)                           # D into bypass
d.arrow([(612, 422), (626, 422)], C.red, dashed=True, sw=1.8)                            # bypass lanes to device

# ---------------- column 3: compensating controls
d.zone(868, 100, 380, 470, "Compensating controls", icon="shield-check")
d.card(884, 140, 348, 92, "For B · govern the apps", ["restrict and review app registrations holding Intune device-management Graph permissions every quarter; Conditional Access for workload identities"],
       badge="B", badge_color=C.red, accent=C.red, shadow=False, body_size=11.5)
d.card(884, 248, 348, 92, "For C · create all three policies", ["Device wipe, retire and delete, same approver group, same approve-then-Complete handshake to activate each one"],
       badge="C", badge_color=C.gold, accent=C.gold, shadow=False, body_size=11.5)
d.card(884, 356, 348, 92, "For D · physical and device-level controls", ["the gate governs admin actions in Intune only; the device itself needs its own protection"],
       badge="D", badge_color=C.grey, accent=C.grey, shadow=False, body_size=11.5)
d.card(884, 464, 348, 92, "For the notification gap", ["no native alert and requests expire after three days; a Logic App or Power Automate flow on the Intune audit log alerts the approver group"],
       badge="!", badge_color=C.blue, accent=C.blue, shadow=False, body_size=11.5)
d.arrow([(822, 422), (848, 422), (848, 186), (884, 186)], C.red, dashed=True, sw=1.4)

# ---------------- bottom
d.callout(32, 590, 1216, 92, "Quarterly review, and what the mapping does not claim", kind="info", icon="calendar",
          body=["Review approver group membership and the app registrations with Intune device-management Graph permissions every quarter; re-validate against current MAA capability yearly.",
                "The control supports AC-3(2) dual authorization and AC-5 separation of duties; full coverage needs the compensating controls above. MAA governs admin actions and is not an electronic-records system."])

d.note_bottom("4 paths, 1 gated natively, 3 compensated; 3 policy types; requests expire after 3 days. Controls: AC-3(2), AC-5, AC-6(9), AU-2, AU-12, CM-5.")
d.render(repo_path("endpoint-management/diagrams/sop-em-003-2.svg"))
