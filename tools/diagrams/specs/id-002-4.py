import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Mover: what moves by itself, what stays, and what people must review",
            "A job change flows from HR as new attributes; birthright access follows them automatically, while requested access and roles only move when a person decides.",
            height=740)

# ---- top: the trigger chain
d.zone(32, 100, 1216, 118, "What a role change sets in motion", icon="arrows-lr", note="WF-M1 job change workflow")
chain = [
    ("HR records the change", ["new department, jobTitle, manager"], "id-card", C.teal),
    ("Attributes flow to Entra ID", ["raise it with HR if they have not; never hand-edit"], "entra-user", C.blue),
    ("WF-M1 fires", ["emails both managers; opens a ServiceNow review task"], "sync-purple", C.purple),
    ("Check and review", ["old group gone, new one present; packages and roles reviewed"], "checklist-purple", C.gold),
]
x = 48
for i, (t, b, ic, col) in enumerate(chain):
    d.card(x, 140, 280, 64, t, b, icon=ic, accent=col, badge=str(i + 1), shadow=False, body_size=11)
    if i < 3:
        d.arrow([(x + 280, 172), (x + 296, 172)], C.grey)
    x += 296

# ---- three columns
cw, gap = 392, 20
x1, x2, x3 = 32, 32 + cw + gap, 32 + 2 * (cw + gap)
top = 236
d.zone(x1, top, cw, 352, "Moves by itself", icon="refresh-green", fill=C.greentint, stroke=C.green, title_color=C.green, note="birthright")
d.card(x1 + 16, top + 44, cw - 32, 64, "Department dynamic group", ["GRP-Dept-<old> drops the user, GRP-Dept-<new> picks them up on the new attribute"], accent=C.green, shadow=False, body_size=11.5)
d.card(x1 + 16, top + 120, cw - 32, 64, "Department site and Teams", ["granted through the department group, so they follow the group change"], accent=C.green, shadow=False, body_size=11.5)
d.card(x1 + 16, top + 196, cw - 32, 64, "Manager for approvals", ["new manager attribute drives future approvals and TAP delivery"], accent=C.green, shadow=False, body_size=11.5)
d.card(x1 + 16, top + 272, cw - 32, 64, "Birthright of the old role", ["disappears when the attributes change; nothing to revoke by hand"], accent=C.green, shadow=False, body_size=11.5)

d.zone(x2, top, cw, 352, "Stays as it is", icon="lock", note="same person, same record")
d.card(x2 + 16, top + 44, cw - 32, 64, "Account and employeeId", ["one account for life; the HR number is never reused"], accent=C.grey, shadow=False, body_size=11.5)
d.card(x2 + 16, top + 120, cw - 32, 64, "Standard licence", ["inherited from GRP-AllEmployees; employeeType unchanged"], accent=C.grey, shadow=False, body_size=11.5)
d.card(x2 + 16, top + 196, cw - 32, 64, "Mailbox and Teams", ["company-wide birthright: email and Teams continue uninterrupted"], accent=C.grey, shadow=False, body_size=11.5)
d.card(x2 + 16, top + 272, cw - 32, 64, "WF-M1 changes nothing itself", ["it emails both managers and opens the review task; removal is a human decision"], accent=C.grey, shadow=False, body_size=11.5)

d.zone(x3, top, cw, 352, "People must review", icon="warning", fill=C.goldtint, stroke=C.gold, title_color=C.gold, note="requested access")
d.card(x3 + 16, top + 44, cw - 32, 64, "Access packages", ["ask the old manager what to keep; remove the rest in Entitlement management"], accent=C.gold, shadow=False, body_size=11.5)
d.card(x3 + 16, top + 120, cw - 32, 64, "Admin roles and PIM eligibility", ["Roles and administrators; roles never move automatically"], accent=C.gold, shadow=False, body_size=11.5)
d.card(x3 + 16, top + 196, cw - 32, 64, "Directly granted access", ["a site or group given outside birthright or a package keeps following the user"], accent=C.red, shadow=False, body_size=11.5)
d.card(x3 + 16, top + 272, cw - 32, 64, "Old group gone, new one present", ["confirm it in the user's Groups rather than assume the rule has caught up"], accent=C.gold, shadow=False, body_size=11.5)

d.callout(32, 604, 1216, 68, "Movers who keep old access are the most common AC-2 audit finding", kind="warn",
          body=["Grant sites only through birthright groups or access packages, so a change of department takes the old access away without a ticket."])

d.note_bottom("Workflow WF-M1: job change → email both managers, ServiceNow review task. Controls: AC-2, AC-6, PS-5; ISO/IEC 27001 5.18, 6.5; SOX logical access.")
d.render(repo_path("identity-access/diagrams/sop-id-002-4.svg"))
