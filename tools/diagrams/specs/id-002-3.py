import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Joiner day zero: from HR record to first sign-in",
            "The HR feed creates the account, dynamic groups and group licensing give birthright access, and a one-time Temporary Access Pass gets the starter to their own MFA.",
            height=790)

actors = [("HR feed", "id-card", C.teal), ("Entra ID", "entra-user", C.blue), ("Identity admin · workflows", "user", C.purple),
          ("Manager", "users", C.gold), ("New starter", "laptop", C.green)]
msgs = [
    (0, 1, "hire record: employeeId, hire date, department, manager, employeeType", C.teal, False),
    (1, 1, "account created from HR, disabled until the start date", C.blue, False),
    (1, 1, "dynamic groups: GRP-Dept-*, GRP-AllEmployees", C.blue, False),
    (1, 1, "group licence Inherited; needs usageLocation", C.blue, False),
    (2, 1, "pre-hire check (WF-J1, hire date minus 7): attributes, groups, licence", C.purple, True),
    (2, 1, "day one: Account enabled = Yes (WF-J2: enable, welcome, groups)", C.purple, False),
    (2, 1, "add Temporary Access Pass: 8 hours, one-time use", C.purple, False),
    (2, 3, "pass by phone or in person, never email; log issued, not the value", C.purple, False),
    (3, 4, "pass handed over at the start", C.gold, False),
    (4, 1, "sign in with the pass at aka.ms/mysecurityinfo", C.green, False),
    (4, 1, "register Microsoft Authenticator or a passkey", C.green, False),
    (1, 4, "pass consumed; from now on the registered method satisfies CA003", C.blue, True),
    (4, 4, "sign in to Windows (SOP-EM-004)", C.green, False),
]
bottom = d.sequence(32, 100, 1216, actors, msgs, lane_h=34)

y = bottom + 10
d.card(32, y, 388, 70, "Never create a second account", ["Verify the HR-created one. If HR and the directory disagree, fix the HR record and let it flow"], icon="x-circle", accent=C.red, shadow=False, body_size=11.5)
d.card(446, y, 388, 70, "Birthright follows attributes", ["Email, Teams, department site, standard licence; every rule tests accountEnabled, so a disabled leaver drops out"], icon="group-window", accent=C.blue, shadow=False, body_size=11.5)
d.card(860, y, 388, 70, "Requested access is separate", ["Finance apps, project sites and every admin role come from an access package with approval and expiry"], icon="checklist-purple", accent=C.purple, shadow=False, body_size=11.5)

d.note_bottom("Attributes from HR: employeeId (immutable), employeeHireDate (UTC), department and jobTitle (HR code lists), manager, employeeType. Controls: AC-2, AC-6, PS-4; ISO 5.16, 5.18.")
d.render(repo_path("identity-access/diagrams/sop-id-002-3.svg"))
