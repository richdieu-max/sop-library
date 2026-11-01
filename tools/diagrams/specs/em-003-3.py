import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Approval state machine: who moves a request, and what the clock does",
            "Every protected action, and the activation of each access policy, walks the same states; the initiator and the approver are always two different people.",
            height=700)

# ---------------- states
d.zone(32, 100, 1216, 330, "States of one request", icon="sync-purple", note="solid arrows: a person acts · dashed: time acts")
# row 1
d.card(48, 150, 220, 96, "Submitted", ["the initiator presses Request for wipe (or retire, delete), adds a justification and submits"],
       badge="1", accent=C.blue, pill=("initiator", C.blue))
d.card(330, 150, 220, 96, "Pending", ["visible under All requests; nobody is told unless the audit-log flow alerts the approver group"],
       badge="2", accent=C.gold, pill=("waiting", C.gold))
d.card(612, 150, 220, 96, "Approved", ["a different admin reviews the device and the reason, adds notes, approves"],
       badge="3", accent=C.green, pill=("approver", C.green))
d.card(894, 150, 338, 96, "Completed: the action runs", ["the initiator opens My requests and selects Complete; only now does the wipe, retire or delete execute"],
       badge="4", accent=C.ink, pill=("initiator", C.ink))
# row 2 (terminal states)
d.card(612, 300, 220, 96, "Rejected", ["the approver declines with notes; nothing happens to the device"],
       badge="×", badge_color=C.red, accent=C.red, pill=("approver", C.red))
d.card(330, 300, 220, 96, "Expired", ["no decision within three days; the request lapses and must be resubmitted"],
       badge="⏱", badge_color=C.grey, accent=C.grey, pill=("3 days", C.grey))

# transitions
d.arrow([(268, 198), (330, 198)], C.blue, label="submit")
d.arrow([(550, 198), (612, 198)], C.green, label="approve")
d.arrow([(832, 198), (894, 198)], C.ink, label="Complete")
d.arrow([(722, 246), (722, 300)], C.red, label="reject")
d.arrow([(440, 246), (440, 300)], C.grey, dashed=True, label="3 days pass")
d.arrow([(330, 348), (300, 348), (300, 210), (300, 198)], C.grey, dashed=True, label="resubmit", label_dy=-14)

# guard note
d.callout(894, 268, 338, 140, "Guards on every arrow", kind="warn", icon="users",
          body=["The initiator can never approve their own request, Global Administrators included.", "Approvers must be members of the Security group, and that group must hold an Intune role with device-action Read; owners cannot approve."])

# ---------------- the same machine activates a policy
d.zone(32, 446, 700, 170, "The same handshake switches each policy on", icon="policy-shield")
d.card(48, 486, 212, 112, "Create the policy", ["Device wipe, retire or delete, approvers = the group, with a justification"], badge="1", accent=C.blue, shadow=False, body_size=11.5)
d.arrow([(260, 542), (274, 542)], C.blue, sw=1.6)
d.card(276, 486, 212, 112, "Other admin approves", ["under All requests; creating the policy is itself a protected change"], badge="2", accent=C.green, shadow=False, body_size=11.5)
d.arrow([(488, 542), (502, 542)], C.green, sw=1.6)
d.card(504, 486, 212, 112, "Creator: Complete", ["under My requests; the gate is live only after this step"], badge="3", accent=C.ink, shadow=False, body_size=11.5)

# ---------------- audit record
d.zone(756, 446, 492, 170, "What the audit log keeps", icon="doc-check-green")
d.card(772, 486, 112, 112, "Initiator", ["who asked, and the justification"], accent=C.blue, shadow=False, title_size=12.5, body_size=11)
d.card(892, 486, 112, 112, "Approver", ["who decided, and the notes"], accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.card(1012, 486, 112, 112, "Timestamps", ["submitted, decided, completed"], accent=C.gold, shadow=False, title_size=12.5, body_size=11)
d.card(1132, 486, 100, 112, "Outcome", ["approved, rejected or expired"], accent=C.purple, shadow=False, title_size=12.5, body_size=11)

d.note_bottom("6 states, 2 roles, 1 timer (3 days). Verify: a test wipe shows Request for wipe; self-approval fails; a group member whose group holds the role can approve. Controls: AC-3(2), AC-5, AU-2, AU-12.")
d.render(repo_path("endpoint-management/diagrams/sop-em-003-3.svg"))
