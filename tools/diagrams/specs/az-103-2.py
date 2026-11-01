import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("STRIDE at every trust boundary: the grid the workshop fills in",
            "Six boundaries down, six questions across; every cell is asked, a real threat becomes one CSV row with its control and evidence, and a threat with no control stays empty as a gap.",
            height=846)

# ---- the grid
bx, by = 32, 100
rows = [("B1", "Internet to gateway", "user and webhook HTTPS"),
        ("B2", "Gateway to app VM", "HTTP on the app port"),
        ("B3", "App VM to Key Vault", "secret reads, private endpoint"),
        ("B4", "App VM to internet egress", "calls to integrations on 443"),
        ("B5", "Operator to control plane", "role, policy, resource writes"),
        ("B6", "Backup to paired region", "recovery points")]
cols = [("S", "Spoofing", "pretend to be a trusted caller?"), ("T", "Tampering", "change data in transit or at rest?"),
        ("R", "Repudiation", "deny doing it, for lack of a log?"), ("I", "Info. disclosure", "data reach someone who should not see it?"),
        ("D", "Denial of service", "overwhelm or cut off the service?"), ("E", "Elevation", "a low role become a high one?")]
label_w, cell_w, cell_h, head_h = 296, 150, 60, 58
d.zone(bx, by, label_w + 6 * cell_w + 20, head_h + 6 * cell_h + 28, None, fill="#fff")
gx = bx + 10 + label_w
for ci, (letter, name, q) in enumerate(cols):
    cx = gx + ci * cell_w
    d.parts.append(f'<rect x="{cx}" y="{by + 10}" width="{cell_w - 4}" height="{head_h - 6}" rx="4" fill="{C.zone}" stroke="{C.border}"/>')
    d.badge(cx + 16, by + 26, letter, C.purple, r=10, size=11)
    d.text(cx + 32, by + 30, name, 11, 600, C.ink, max_w=cell_w - 40)
    d.lines(cx + 8, by + 44, q, 10, cell_w - 14, 400, C.grey, lh=11)
for ri, (bid, bname, crosses) in enumerate(rows):
    ry = by + head_h + 10 + ri * cell_h
    d.card(bx + 10, ry, label_w - 6, cell_h - 6, f"{bid} · {bname}", [crosses], accent=C.blue, shadow=False, title_size=12, body_size=10.5)
    for ci in range(6):
        cx = gx + ci * cell_w
        d.parts.append(f'<rect x="{cx}" y="{ry}" width="{cell_w - 4}" height="{cell_h - 6}" rx="4" fill="#FCFCFB" stroke="{C.rule}"/>')
        d.text(cx + (cell_w - 4) / 2, ry + 34, "ask", 10.5, 400, C.light, "middle")
# the two worked rows from the runbook template
def filled(ri, ci, control, gap, rating, col):
    ry = by + head_h + 10 + ri * cell_h; cx = gx + ci * cell_w
    d.parts.append(f'<rect x="{cx}" y="{ry}" width="{cell_w - 4}" height="{cell_h - 6}" rx="4" fill="{C.redtint}" stroke="{col}" stroke-width="1.4"/>')
    d.text(cx + 6, ry + 16, control, 10, 600, C.ink, max_w=cell_w - 62)
    d.lines(cx + 6, ry + 31, gap, 10, cell_w - 14, 400, C.grey, lh=12)
    d.pill(cx + cell_w - 50, ry + 5, rating, col, size=9.5)
filled(0, 0, "WAF rate limit", "on /api/auth; gap: WAF in Detection until UAT ends", "High", C.red)
filled(3, 3, "NAT + NSG 443", "outbound only; gap: no FQDN allow-list", "High", C.red)

# ---- below the grid: rating and the rules
gy = by + head_h + 10 + 6 * cell_h + 40
d.zone(32, gy, 440, 200, "Rating: likelihood × impact", icon="heatmap")
hm = 150
d.text(hm - 6, gy + 50, "impact →", 10.5, 400, C.grey, "end")
for j, im in enumerate([1, 2, 3]):
    d.text(hm + j * 52 + 22, gy + 50, str(im), 11, 600, C.ink, "middle")
for i, lk in enumerate([3, 2, 1]):
    d.text(hm - 8, gy + 76 + i * 40, f"L {lk}", 11, 600, C.ink, "end")
    for j, im in enumerate([1, 2, 3]):
        score = lk * im
        col = C.red if score >= 7 else (C.gold if score >= 4 else C.green)
        d.status_cell(hm + j * 52, gy + 58 + i * 40, 44, 34, str(score), col)
d.text(hm + 172, gy + 76, "7–9 High", 11, 600, C.red); d.text(hm + 172, gy + 116, "4–6 Medium", 11, 600, C.gold); d.text(hm + 172, gy + 156, "1–3 Low", 11, 600, C.green)
d.text(46, gy + 190, "Every High row gets a risk register ID and an owner role.", 10.5, 400, C.grey)

d.zone(492, gy, 756, 200, "Rules at the grid", icon="checklist-purple")
d.card(506, gy + 40, 236, 136, "No control, no guess", ["Leave the control column empty: that is a gap, and gaps are what the client signs off"], accent=C.red, shadow=False, title_size=12, body_size=11)
d.card(754, gy + 40, 236, 136, "Evidence, not a name", ["Each control names an evidence file that exists and is hashed (inventory JSON, WAF policy export)"], accent=C.green, shadow=False, title_size=12, body_size=11)
d.card(1002, gy + 40, 232, 136, "Data at risk now: one day", ["An open inbound rule to a data port is reported to the client within one business day, not held for the final report"], accent=C.gold, shadow=False, title_size=12, body_size=11)

d.note_bottom("Two cells show the worked rows from SOP-03-threat-model.template.csv; every other cell is asked in the workshop. Controls: RA-3, SA-8, SA-11; CSF ID.RA; ISO A.5.7, A.8.27.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-103-2.svg"))
