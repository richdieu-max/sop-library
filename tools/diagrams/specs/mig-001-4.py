import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("The cutover window hour by hour, with the go / no-go gates",
            "Four hours, six timed steps, and a decision at 11:30 that leaves 30 minutes to roll back to a source VM that was only ever shut down.",
            height=814)

# ---------------- the clock strip
d.zone(32, 100, 1216, 332, "08:00 to 12:00: the approved window (change 2)", icon="clock", note="DNS TTL was lowered the day before; the SME is booked for the whole window")
x0, x1 = 80, 1200
def px(hhmm):
    h, m = map(int, hhmm.split(":"))
    return x0 + (x1 - x0) * ((h - 8) * 60 + m) / 240
d.parts.append(f'<rect x="{x0}" y="{248}" width="{x1 - x0}" height="8" rx="4" fill="{C.blue}" opacity="0.25"/>')
for t in ("08:00", "09:00", "10:00", "11:00", "12:00"):
    d.line(px(t), 240, px(t), 264, C.blue, 2)
    d.text(px(t), 282, t, 11.5, 600, C.ink, "middle")
events = [
    ("08:00", "Freeze", ["announce; stop BarTender and Integration services"], C.red, True),
    ("08:15", "Final sync and launch", ["wait for zero lag, launch the cutover instance, shut down (keep) the source"], C.blue, False),
    ("09:00", "Network", ["DNS A record to the cloud private IP; routes and firewall for 9100; SQL and AD reachable"], C.blue, True),
    ("09:30", "Licence and first labels", ["re-activate; print a test label on every production printer"], C.gold, False),
    ("10:15", "SME validation", ["dev, test and prod printing; largest template at normal speed; integrations fire"], C.purple, True),
    ("11:30", "Decision", ["finalize, or roll back with 30 minutes left in the window"], C.green, False),
]
for t, title, body, col, above in events:
    x = px(t)
    d.parts.append(f'<circle cx="{x:.0f}" cy="252" r="7" fill="{col}" stroke="#fff" stroke-width="2"/>')
    bw = 196
    bx = min(max(x - 30, 48), 1232 - bw)
    if above:
        by = 148
        d.line(x, 240, x, by + 76, col, 1.2)
        d.card(bx, by, bw, 76, title, body, accent=col, shadow=False, title_size=12.5, body_size=10.5)
        d.text(bx + 8, by - 4, t, 11, 600, col)
    else:
        by = 304
        d.line(x, 264, x, by, col, 1.2)
        d.card(bx, by, bw, 76, title, body, accent=col, shadow=False, title_size=12.5, body_size=10.5)
        d.text(bx + 8, by + 90, t, 11, 600, col)
d.text(px("11:30") + 12, 276, "30 min reserve", 10.5, 400, C.green)
d.parts.append(f'<rect x="{px("11:30"):.0f}" y="248" width="{px("12:00") - px("11:30"):.0f}" height="8" rx="4" fill="{C.green}" opacity="0.5"/>')

# ---------------- gates and rollback
d.zone(32, 448, 596, 300, "What must be true at each gate", icon="checklist-purple")
gates = [("09:00", "launch booted; zero replication lag before it; source is off, not deleted", C.blue),
         ("09:30", "DNS resolves to the private IP; 9100 and SNMP 161/UDP reach every printer; domain logon works", C.blue),
         ("10:15", "licence active with the expected seats; a label printed on each production printer", C.gold),
         ("11:30", "SME signs off every verify row; otherwise roll back now, not at 11:59", C.green)]
yy = 488
for t, body, col in gates:
    d.card(48, yy, 564, 56, t, [body], badge="✓", badge_color=col, accent=col, shadow=False, title_size=12.5, body_size=11)
    yy += 64

d.zone(652, 448, 596, 300, "Roll back, in this order (minutes, not hours)", icon="lightning", fill=C.redtint, stroke=C.red, title_color=C.red)
rb = [("Stop the cloud instance, keep it", "it holds the evidence of what failed"),
      ("Power on the source", "start BarTender services; confirm or re-activate the licence on the source"),
      ("Revert the network", "DNS record back; undo any printer route or firewall change"),
      ("Notify and record", "tell users; write the reason into the change. MGN: back to Ready for testing with replication resumed; Azure: replication keeps running until removed")]
yy = 488
for i, (t, body) in enumerate(rb):
    d.card(668, yy, 564, 56 if i < 3 else 60, t, [body], badge=str(i + 1), badge_color=C.red, accent=C.red, shadow=False, title_size=12.5, body_size=11)
    yy += 64

d.note_bottom("On success: Finalize cutover (MGN) or Complete migration (Azure), enable backup and patching, archive the replication later. Controls: CM-3, CP-10, AU-2 (every migration action logged).")
d.render(repo_path("cloud-migration/diagrams/sop-mig-001-4.svg"))
