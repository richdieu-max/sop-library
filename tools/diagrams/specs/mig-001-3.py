import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Choosing the method: AWS MGN, Azure Migrate or a rebuild",
            "Rehost is the default for a validated label server: block replication keeps the validated state identical. The target cloud picks the tool; only an unsupported or drifted OS justifies a rebuild.",
            height=892)

# ---------------- decision ladder
d.zone(32, 100, 1216, 128, "Two questions decide it", icon="question-diamond-gold")
d.card(48, 140, 360, 74, "Is the OS in support and the build clean?", ["No, drift is heavy or an upgrade is due: rebuild (C) and plan fuller re-validation"],
       icon="question-diamond", accent=C.gold, shadow=False, body_size=11.5)
d.arrow([(408, 177), (440, 177)], C.green, label="yes")
d.card(442, 140, 380, 74, "Which cloud holds the landing zone?", ["Rehost where the landing zone and private link are: AWS → MGN (A); Azure → Azure Migrate (B)"],
       icon="cloud", accent=C.blue, shadow=False, body_size=11.5)
d.arrow([(822, 177), (854, 177)], C.blue)
d.card(856, 140, 376, 74, "Rehost, then re-test only what changed", ["the network path, the licence and the hardware the OS sees; templates and drivers are byte for byte the same"],
       icon="check-circle", accent=C.green, shadow=False, body_size=11.5)

# ---------------- three method columns
cols = [("A", "AWS Application Migration Service", C.gold), ("B", "Azure Migrate", C.blue), ("C", "Rebuild and replatform", C.purple)]
xs = [262, 586, 910]
CW = 310
d.zone(32, 244, 1216, 474, "Method by method", icon="arrows-lr", note="same discovery, same freeze rule, same cutover window for A and B")
for (letter, name, col), x in zip(cols, xs):
    d.card(x, 284, CW, 44, name, [], badge=letter, badge_color=col, accent=col, shadow=False, title_size=13)
rows = [
    ("How it copies", ["agent on the source replicates all disks: initial sync, then changed blocks, while BarTender runs", "appliance OVA on vCenter replicates the VM from vSphere; no agent in the guest", "fresh hardened image; restore the System Database, robocopy /MIR /COPYALL documents, Librarian and integrations"]),
    ("What it needs open", ["TCP 1500 source → staging subnet; 443 source → MGN endpoint and S3; private IP replication on", "TCP 902 appliance → ESXi hosts; vCenter role with read, snapshot, disk and change-tracking", "the same printer driver versions: a different driver, dpi or font shifts barcodes"]),
    ("Access, just in time", ["Identity Center permission sets: MigrationFullAccess, AgentInstallationPolicy on short-lived credentials", "Owner, or Contributor + User Access Administrator, for project and appliance; subnets/join/action on the VNet", "local Administrator, BarTender administrator, SQL db_owner (sysadmin for restore)"]),
    ("Test before cutover", ["Launch test instances into a subnet that cannot reach production printers; repeat as needed; Mark Ready for cutover", "Test migration into an isolated test VNet, Azure Bastion, then Clean up test migration", "side-by-side print comparison against the source on every printer"]),
    ("Cutover action", ["Launch cutover instances, shut down (keep) the source, DNS, licence, validate, Finalize, later Archive", "Migrate with Yes to shut down the source (planned, no data loss), DNS, licence, validate, Complete migration", "move the licence, recreate printers on DNS-named ports, cut DNS; the old server stays off but intact"]),
    ("Scripted as", ["aws mgn start-test, change-server-life-cycle-state, start-cutover, finalize-cutover, or AWS.Tools.Mgn", "Invoke-AzMigrateLabelServer.ps1 -Stage Replicate · Test · CleanupTest · Migrate · Complete, one stage per change step", "build automation of the landing zone; the content moves by hand with evidence"]),
    ("Re-validation", ["network path, licence, hardware the OS sees", "network path, licence, hardware the OS sees", "full: OS, SQL, drivers, templates, integrations"]),
]
yy = 340
for label, cells in rows:
    d.text(48, yy + 16, label, 12.5, 600, C.ink)
    d.line(48, yy + 50, 1232, yy + 50, C.rule, 1)
    for (letter, name, col), x, cell in zip(cols, xs, cells):
        d.lines(x + 4, yy + 14, cell, 10.5, CW - 8, 400, C.grey, lh=13)
    yy += 54

# ---------------- bottom strip: constants
d.zone(32, 734, 1216, 96, "The same for every method", icon="shield-check")
consts = [("Discovery first", "Get-LabelServerDependencies.ps1: IPs and UNC paths become DNS names", C.blue),
          ("Disk-change freeze", "from agent install until cutover; exceptions go back to the CAB", C.red),
          ("Right-size", "reference source at 92 % CPU on 2 vCPU / 8 GB went to 4 vCPU / 16 GB", C.teal),
          ("Licence", "deactivate before, re-activate after; TCP 5160 for remote licence clients", C.gold)]
x = 48
for t, b, col in consts:
    d.card(x, 768, 290, 54, t, [b], accent=col, shadow=False, title_size=12, body_size=10)
    x += 298

d.note_bottom("Elapsed: 2–3 weeks, with a 4-hour cutover window and a source VM that is only ever shut down, never modified. Controls: CM-3 (two changes), CP-10 (retained source), SC-28 (encrypted replicated disks).")
d.render(repo_path("cloud-migration/diagrams/sop-mig-001-3.svg"))
