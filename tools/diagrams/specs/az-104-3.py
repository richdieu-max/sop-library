import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Role-to-permission matrix: five groups, three scopes, nothing on a person",
            "Each sg-az group holds one role at one scope; a role set at the root is inherited by Platform and Customers, and a test account per group proves one allowed and one denied action.",
            height=840)

# ---- grid: rows = groups, cols = scopes
gx, gy = 32, 100
label_w, col_w, row_h, head_h = 330, 278, 78, 54
scopes = [("<org>-<product> root", "inherited by every group below it"), ("Platform", "shared services, hub, logging"), ("Customers", "every customer stamp")]
groups = [
    ("-owners", "the engagement owners", "Owner", 0, "eligible · PIM · 4 h", C.red, True),
    ("-platform-ops", "platform operators", "Contributor", 1, "standing", C.purple, False),
    ("-customer-ops", "customer operators", "Contributor", 2, "eligible · PIM · 8 h", C.gold, True),
    ("-security", "security team", "Security Reader + Reader", 0, "standing", C.teal, False),
    ("-auditors", "auditors", "Reader", 0, "standing", C.blue, False),
]
d.zone(gx, gy, label_w + 3 * col_w + 24, head_h + 5 * row_h + 26, None, fill="#fff")
for ci, (sname, snote) in enumerate(scopes):
    cx = gx + 12 + label_w + ci * col_w
    d.parts.append(f'<rect x="{cx}" y="{gy + 10}" width="{col_w - 8}" height="{head_h - 8}" rx="4" fill="{C.zone}" stroke="{C.border}"/>')
    d.icon(cx + 8, gy + 20, "hierarchy" if ci == 0 else "folder", 0.42)
    d.text(cx + 34, gy + 29, sname, 12, 600, C.ink, max_w=col_w - 50)
    d.text(cx + 34, gy + 44, snote, 10.5, 400, C.grey, max_w=col_w - 50)
for ri, (g, who, role, at, mode, col, pim) in enumerate(groups):
    ry = gy + head_h + 10 + ri * row_h
    d.card(gx + 12, ry, label_w - 8, row_h - 8, f"sg-az-<org>-<product>{g}", [who], accent=col, shadow=False, title_size=12, body_size=11, icon="users")
    for ci in range(3):
        cx = gx + 12 + label_w + ci * col_w
        inherited = (ci > at) and at == 0
        if ci == at:
            d.parts.append(f'<rect x="{cx}" y="{ry}" width="{col_w - 8}" height="{row_h - 8}" rx="4" fill="{"#FFF8F8" if pim else "#fff"}" stroke="{col}" stroke-width="1.4"/>')
            d.text(cx + 10, ry + 22, role, 12, 600, col, max_w=col_w - 20)
            d.pill(cx + 10, ry + 32, mode, col, solid=pim, size=10)
        elif inherited:
            d.parts.append(f'<rect x="{cx}" y="{ry}" width="{col_w - 8}" height="{row_h - 8}" rx="4" fill="#FCFCFB" stroke="{C.rule}" stroke-dasharray="4 3"/>')
            d.text(cx + 10, ry + 30, f"{role}", 11, 400, C.grey, max_w=col_w - 20)
            d.text(cx + 10, ry + 46, "inherited from the root", 10.5, 400, C.light)
        else:
            d.parts.append(f'<rect x="{cx}" y="{ry}" width="{col_w - 8}" height="{row_h - 8}" rx="4" fill="#FCFCFB" stroke="{C.rule}"/>')
            d.text(cx + (col_w - 8) / 2, ry + 40, "no role here", 10.5, 400, C.light, "middle")

# ---- bottom: how the matrix is proven, and the exception
by = gy + head_h + 5 * row_h + 60
d.zone(32, by, 740, 170, "The matrix test: one allowed and one denied action per group", icon="doc-check-green", note="SOP-04 matrix log")
d.table(46, by + 40, [86, 110, 176, 72, 180, 92], [
    ["Role", "Account", "Action", "Expected", "Actual", "Logged"],
    ["auditors", "test-auditor", "Read policy compliance", "Allow", "Allow", "UTC, corr. ID"],
    ["auditors", "test-auditor", "Delete a lock", "Deny", "Deny (AuthorizationFailed)", "UTC, corr. ID"],
], row_h=26, size=11)
d.text(46, by + 150, "One test account per group, approved in advance; the activity log correlation ID is the evidence for every row.", 10.5, 400, C.grey, max_w=712)

d.zone(792, by, 456, 170, "Resource Policy Contributor: only on request", icon="policy-shield", fill=C.goldtint, stroke=C.gold, title_color=C.gold, dashed=True)
d.lines(806, by + 44, "platform-ops may also hold Resource Policy Contributor at the root, but only when the client asks in writing. Readers and auditors never get a write role; the owners group is the only route to Owner, and only through PIM.", 11.5, 428, 400, C.grey)
d.lines(806, by + 118, "A user holding Owner or User Access Administrator directly is a finding unless it is a documented, time-limited exception removed at hand-over.", 11.5, 428, 400, C.ink)

d.note_bottom("Standing: assigned and always active. Eligible: held through PIM and active only after activation (4 h owners, 8 h customer-ops). Controls: AC-2, AC-5, AC-6; ISO A.5.15, A.5.18, A.8.2.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-104-3.svg"))
