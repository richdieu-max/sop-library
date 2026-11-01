import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("What a clone carries, what must change before first use, what is never created",
            "The OS disk is copied byte for byte, so everything inside it comes along; the VM resource around it is built new, and a few things are deliberately left out.",
            height=744)

CAR, NEW, CHG, NEV, MATCH = C.green, C.blue, C.gold, C.red, C.purple
rows = [
    ("Operating system, applications, patch level", CAR, "carried", "Byte-for-byte from the snapshot; the clone boots the same build the source ran"),
    ("Data disks", CAR, "carried", "Only the ones you snapshot (<VM>-DATAsnap-1 ...) and attach in stage 3"),
    ("Local admin credentials", CHG, "change first", "Inherited, since Attach skips first-boot provisioning; Set-LocalUser with a new password"),
    ("Computer name", CHG, "change first", "Rename-Computer on an isolated network before the clone meets production"),
    ("SID and domain trust secret", CHG, "change first", "If the source is domain-joined: unjoin to a workgroup, rename, rejoin; otherwise one of the pair loses its trust"),
    ("Config with hostnames, IPs, connection strings", CHG, "change first", "Search the configuration for the old name; hard-coded values are the usual clone-only failure"),
    ("NIC and private IP", NEW, "new", "Created in the planned VNet and subnet, Delete with VM; NIC NSG None when the subnet has one"),
    ("VM size, zone, tags", NEW, "new", "Chosen for the clone: B-series and Standard SSD for tests; ChangeRef, Owner, Environment, Purpose"),
    ("Boot diagnostics, patch assessment, auto-shutdown", NEW, "new", "Set on the clone (auto-shutdown for non-production)"),
    ("Security profile (Trusted Launch)", MATCH, "must match", "A Trusted Launch disk on a Standard VM lands on the recovery screen; mirror the source profile"),
    ("Public IP", NEV, "never", "No public IP on the VM or NIC; reach it through Bastion or a one-hour JIT request"),
    ("Public disk access", NEV, "never", "Disable public access or use a private endpoint: a disk can otherwise be exported by SAS URL"),
]
d.zone(32, 100, 1216, 60 + 30 * len(rows) + 16, None)
d.text(48, 122, "Item", 11.5, 600, C.ink)
d.text(420, 122, "Status", 11.5, 600, C.ink)
d.text(560, 122, "What that means for the clone", 11.5, 600, C.ink)
d.line(48, 130, 1232, 130, C.border, 1)
yy = 140
for item, col, label, why in rows:
    if (yy - 140) // 30 % 2 == 1:
        d.rect(48, yy - 4, 1184, 30, fill="#FCFCFB", stroke="none", rx=3)
    d.text(48, yy + 14, item, 12, 600, C.ink, max_w=360)
    d.status_cell(420, yy, 120, 22, label, col)
    d.text(560, yy + 14, why, 11.5, 400, C.grey, max_w=670)
    yy += 30

# ---------------- legend + two side notes
ly = yy + 24
d.legend(48, ly, [("carried in the disk", CAR), ("change before first use", CHG), ("new with the VM", NEW), ("must match the source", MATCH), ("never created", NEV)], gap=22)

d.zone(32, ly + 22, 596, 116, "Why the clone looks exactly like the source", icon="ssd", note="specialized clone · methods A, B, C, E")
d.lines(48, ly + 70, "The disk is attached with -CreateOption Attach, so no first-boot provisioning runs: same name, same accounts, same SID. That is right for test copies, upgrade rehearsals and forensic copies, and wrong for two machines on one domain.", 12, 564)

d.zone(652, ly + 22, 596, 116, "When you want a fresh identity instead", icon="sync-purple", note="method D · Compute Gallery")
d.lines(668, ly + 70, "Clone first, then run sysprep.exe /generalize /oobe /shutdown in the clone (never the original: Sysprep is one-way) and capture to the gallery as Generalized. Every VM deployed from it gets new credentials and a new SID.", 12, 564)

d.note_bottom("Snapshot of a running VM is crash-consistent; stop (deallocate) the source for a clean disk. Snapshots and disks bill until deleted. Controls: CP (clone and restore paths); CIS: RDP/SSH never exposed.")
d.render(repo_path("azure-procedures/diagrams/sop-az-003-2.svg"))
