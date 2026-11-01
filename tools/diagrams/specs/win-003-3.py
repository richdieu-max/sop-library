import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path, text_width

d = Diagram("Which SMB dialect you get, why SMB1 stays off, and who maps the drives at scale",
            "The client offers every dialect it has and the server picks the highest both speak; with SMB1 absent the ladder stops at 2.0.2, and Group Policy or Intune does the mapping for everyone.",
            height=840)

# ---------------- left: negotiation + dialect ladder
d.zone(32, 100, 620, 404, "NEGOTIATE: the highest dialect both sides speak", icon="arrows-lr", note="result: Get-SmbConnection Dialect")
d.card(48, 142, 180, 60, "Workstation client", ["MRxSmb20 offers 2.0.2 up to 3.1.1"], icon="monitor", accent=C.blue, shadow=False, title_size=12.5, body_size=11)
d.card(446, 142, 190, 60, "File server or NAS", ["picks the highest dialect it also speaks"], icon="server", accent=C.grey, shadow=False, title_size=12.5, body_size=11)
d.arrow([(228, 162), (446, 162)], C.blue, label="dialects offered", label_dy=-7)
d.arrow([(446, 184), (228, 184)], C.grey, label="dialect chosen", label_dy=12, dashed=True)

# ladder
lx, lw = 48, 588
rungs = [
    ("3.1.1", "Windows 10 and 11, Server 2016 and later", "pre-auth integrity, signing, encryption", C.green, "pass"),
    ("3.0 / 3.0.2", "Windows 8 / Server 2012 era", "encryption available", C.green, "fine"),
    ("2.1 / 2.0.2", "Windows 7 / Server 2008 era", "the lowest an SMB1-free client offers", C.gold, "upgrade the server"),
    ("1.5 (SMB1 / CIFS)", "only if the SMB1 client is installed", "no pre-auth integrity, no encryption", C.red, "exception only"),
]
y = 222
for ver, who, what, col, tag in rungs:
    d.card(lx, y, lw, 54, "", [], accent=col, shadow=False)
    d.text(lx + 16, y + 24, ver, 13.5, 600, C.ink)
    d.text(lx + 16, y + 42, who, 10.5, 400, C.grey)
    d.text(lx + 236, y + 24, what, 11, 400, C.ink, max_w=230)
    pw = text_width(tag, 10.5, 600) + 16
    d.pill(lx + lw - 12 - pw, y + 17, tag, col)
    y += 62
d.text(lx + 16, 480, "Dialect 1.5 in Get-SmbConnection names the server that still needs upgrading; 3.1.1 is the pass condition.", 10.5, 400, C.grey, max_w=560)
d.text(lx + 16, 496, "Windows 11 24H2 also requires signing and blocks guest logons: fix the NAS, not the client.", 10.5, 400, C.grey, max_w=560)

# ---------------- right: why SMB1 stays off and the toggle cycle
d.zone(676, 100, 572, 404, "Why SMB1 stays off, and what the feature toggle does to the list", icon="shield-x", fill=C.redtint, stroke=C.red, dashed=True, title_color=C.red)
d.card(692, 142, 540, 64, "SMB1 has no pre-authentication integrity and no encryption", ["the target of MS17-010 (EternalBlue, WannaCry, NotPetya); not installed by default since Windows 10 version 1709"], icon="warning", accent=C.red, shadow=False, title_size=12.5, body_size=11)
# cycle of four cards
cyc = [("Feature off", "Windows rewrites the dependency list consistently: Bowser / MRxSmb20 / NSI. This is the repair.", C.green, "repair"),
       ("Exception on", "SMB1 Client only: MRxSmb10 added; record the device, exception reference and replacement date", C.gold, "time-boxed"),
       ("Automatic Removal", "SMB1 removed again later, but a stale list may still name MRxSmb10", C.red, "1068 again"),
       ("Fix the list itself", "sc config LanmanWorkstation depend= Bowser/MRxSmb20/NSI, then restart the service", C.blue, "step 6")]
pos = [(692, 222), (972, 222), (972, 338), (692, 338)]
for (t, b, col, tag), (cx, cy) in zip(cyc, pos):
    d.card(cx, cy, 260, 100, t, [b], accent=col, shadow=False, title_size=12.5, body_size=11, pill=(tag, col))
d.arrow([(952, 272), (972, 272)], C.gold, sw=1.6)
d.arrow([(1102, 322), (1102, 338)], C.red, sw=1.6)
d.arrow([(972, 388), (952, 388)], C.blue, sw=1.6)
d.arrow([(822, 338), (822, 322)], C.green, sw=1.6, dashed=True)
d.lines(692, 460, "Turning the feature off is the repair; turning it on only re-introduces SMB1, and it stays off whenever the server speaks SMB 2 or 3. Enabling it needs an approved, scoped, time-boxed exception (risk: high).", 10.5, 540, 400, C.grey, lh=15)

# ---------------- bottom: Method D at scale, GPO vs Intune
d.zone(32, 520, 1216, 250, "Method D · at scale: who does what", icon="devices", note="user context maps drives; SYSTEM context repairs the client")
d.text(362, 560, "Group Policy", 12.5, 600, C.ink, "middle")
d.text(702, 560, "Intune", 12.5, 600, C.ink, "middle")
d.text(1056, 560, "Both", 12.5, 600, C.ink, "middle")
rows = [("Map the drives", "user session", C.blue), ("Keep the client healthy", "SYSTEM", C.purple), ("Stop it coming back", "central", C.green)]
cells = {
    (0, 0): ("GPP Drive Maps", "User Configuration › Preferences; Replace (cures stale maps) or Update; item-level targeting by security group"),
    (0, 1): ("Platform script", "no native drive-map profile: Run using the logged-on credentials = Yes, New-SmbMapping per letter"),
    (1, 1): ("SYSTEM Remediation", "detects MRxSmb10 listed while SMB1 is not enabled, or Workstation not running, and resets the list"),
    (2, 2): ("SMB1 off centrally; fix the package at source", "the package owner corrects it, otherwise it reinstalls and breaks every PC it is assigned to"),
}
col_x = {0: 200, 1: 540, 2: 880}
col_w = {0: 324, 1: 324, 2: 352}
ry = 570
for ri, (rname, ctx, col) in enumerate(rows):
    d.text(48, ry + 22, rname, 12, 600, C.ink)
    d.pill(48, ry + 28, ctx, col)
    for ci in range(3):
        if (ri, ci) in cells:
            t, b = cells[(ri, ci)]
            d.card(col_x[ci], ry, col_w[ci], 62, t, [b], accent=col, shadow=False, title_size=12, body_size=10.5)
        elif not (ri == 2 and ci != 2):
            d.rect(col_x[ci], ry, col_w[ci], 62, fill=C.zone, stroke=C.rule, rx=5)
            d.text(col_x[ci] + col_w[ci] / 2, ry + 35, "—", 12, 400, C.light, "middle")
    ry += 68

d.note_bottom("Dependencies on a current Windows 11 client: Bowser, MRxSmb20, NSI; MRxSmb10 only with the SMB1 client. Controls: CM-7, SC-8, IA-5, AC-6.")
d.render(repo_path("windows-support/diagrams/sop-win-003-3.svg"))
