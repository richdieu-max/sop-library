import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Why a 203 dpi driver shrinks a label designed at 300 dpi",
            "The driver turns the format into a fixed number of dots at its own resolution; the printhead then prints those dots at its real density, so a dpi mismatch scales every label.",
            height=790)

PX = 4.4  # pixels per millimetre, same scale in every panel

# ---------------- top zone: three panels drawn to scale
d.zone(32, 100, 1216, 366, "A 2.0 × 1.0 in label (50.8 × 25.4 mm) through three driver and head pairings", icon="printer",
       note="dashed outline = the label stock · filled block = what the head actually prints")
panels = [
    ("Match: 300 dpi driver on a 300 dpi head", "ZD620-300dpi (ZPL)", "12 dots/mm", 600, 300, 50.8, 25.4, C.green, "100 %", "every field where the format put it"),
    ("Fault: 203 dpi driver on a 300 dpi head", "ZT620-203dpi (ZPL)", "12 dots/mm", 406, 203, 34.4, 17.2, C.red, "68 %", "uniform shrink: 203 ÷ 300 = 0.68"),
    ("Mirror fault: 300 dpi driver on a 203 dpi head", "ZD620-300dpi (ZPL)", "8 dots/mm", 600, 300, 75.1, 37.5, C.gold, "148 %, cropped", "enlarged: 300 ÷ 203 = 1.48, cut at the stock edge"),
]
px0 = 48
for i, (title, drv, head, dw, dh, mmw, mmh, col, ratio, why) in enumerate(panels):
    x = px0 + i * 400
    d.text(x, 160, title, 13, 600, C.ink, max_w=380)
    d.pill(x, 170, "driver: " + drv, C.grey)
    d.pill(x + 180, 170, "head: " + head, C.grey)
    # stock outline
    sx, sy = x + 10, 206
    sw, sh = 50.8 * PX, 25.4 * PX
    d.parts.append(f'<rect x="{sx}" y="{sy}" width="{sw:.0f}" height="{sh:.0f}" rx="3" fill="#fff" stroke="{C.grey}" stroke-width="1.2" stroke-dasharray="5 4"/>')
    # printed block (clipped to the stock for the enlarged case)
    pw, ph = mmw * PX, mmh * PX
    cw, ch = min(pw, sw), min(ph, sh)
    d.parts.append(f'<rect x="{sx}" y="{sy}" width="{cw:.0f}" height="{ch:.0f}" rx="2" fill="{col}" opacity="0.18"/>')
    d.parts.append(f'<rect x="{sx}" y="{sy}" width="{cw:.0f}" height="{ch:.0f}" rx="2" fill="none" stroke="{col}" stroke-width="2"/>')
    # a barcode-like glyph inside the printed block, scaled with it
    scale = cw / sw
    bx = sx + 10 * scale
    for k in range(14):
        bw = (3 if k % 3 else 6) * scale
        d.parts.append(f'<rect x="{bx:.1f}" y="{sy + 14 * scale:.1f}" width="{bw:.1f}" height="{52 * scale:.1f}" fill="{col}"/>')
        bx += bw + 4 * scale
    # text line placeholder
    d.parts.append(f'<rect x="{sx + 10 * scale:.1f}" y="{sy + 78 * scale:.1f}" width="{150 * scale:.1f}" height="{8 * scale:.1f}" rx="2" fill="{col}" opacity="0.7"/>')
    if pw > sw:
        # overflow ghost of the enlarged content beyond the stock
        d.parts.append(f'<rect x="{sx}" y="{sy}" width="{pw:.0f}" height="{ph:.0f}" rx="2" fill="none" stroke="{col}" stroke-width="1" stroke-dasharray="3 3" opacity="0.7"/>')
        d.text(sx + pw, sy + ph + 14, f"{mmw} × {mmh} mm would be printed; the stock ends at 50.8 × 25.4", 10.5, 400, col, "end")
    elif pw < sw:
        d.text(sx + 4, sy + ch + 14, f"{mmw} × {mmh} mm", 10.5, 400, col)
    else:
        d.text(sx + cw + 8, sy + ch / 2 + 4, f"{mmw} × {mmh} mm", 10.5, 400, col)
    d.text(sx, 398, f"{dw} × {dh} dots sent", 11, 600, C.ink)
    d.pill(x + 10, 408, ratio, col, solid=True)
    d.lines(x + 10, 446, why, 11, 370, 400, C.grey)

# ---------------- bottom zone: ruler test
d.zone(32, 482, 1216, 248, "The 50 mm ruler test proves the head; the LIMS reprint proves the queue", icon="ruler",
       note="dots = mm × dpi ÷ 25.4")
d.card(48, 520, 372, 88, "Raw ZPL sent to port 9100", ["^GB590,8,8 draws a bar 590 dots long. The head, not the driver, decides how long 590 dots are."],
       icon="terminal", accent=C.blue)
d.card(48, 618, 372, 100, "Read the head without a ruler", ["Configuration label (FEED + CANCEL, 2 s): 8 dots/mm = 203 dpi, 12 dots/mm = 300 dpi; or ~HI on port 9100, third field = dots/mm."],
       icon="doc-search", accent=C.grey)
# ruler
rx, ry = 452, 534
for mm in range(0, 81, 10):
    px = rx + mm * PX
    d.line(px, ry, px, ry + 12, C.grey, 1)
    d.text(px, ry + 26, f"{mm}", 10, 400, C.grey, "middle")
for mm in range(0, 81, 5):
    px = rx + mm * PX
    d.line(px, ry, px, ry + 6, C.grey, 1)
d.line(rx, ry, rx + 80 * PX, ry, C.grey, 1.5)
d.text(rx + 80 * PX + 8, ry + 10, "mm", 10.5, 400, C.grey)
bars = [("300 dpi head (12 dots/mm): 590 dots = 50.0 mm", 50.0, C.green, "pass"),
        ("203 dpi head (8 dots/mm): 590 dots = 73.8 mm", 73.8, C.red, "203 dpi head")]
yy = 578
for label, mm, col, pill in bars:
    d.parts.append(f'<rect x="{rx}" y="{yy}" width="{mm * PX:.0f}" height="16" rx="3" fill="{col}"/>')
    d.text(rx, yy + 34, label, 11.5, 600, C.ink)
    d.pill(rx + mm * PX + 10, yy - 2, pill, col)
    yy += 60
d.callout(900, 520, 332, 198, "Reading the diagnosis ratio", kind="info", icon="question-diamond",
          body=["Bad label ÷ good label ≈ 0.68: a 203 dpi driver on a 300 dpi head.",
                "≈ 1.48: a 300 dpi driver on a 203 dpi head, enlarged and cropped.",
                "Drifting position or random cropping is media calibration, not dpi."])

d.note_bottom("Fix lives on the print server: swap the queue's driver (Set-Printer -DriverName), keep the port and queue name, then ruler test and LIMS reprint. Controls: CM-2, CM-3, CM-6.")
d.render(repo_path("label-printing/diagrams/sop-lbl-001-3.svg"))
