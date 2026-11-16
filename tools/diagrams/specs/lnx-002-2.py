import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("When a patch breaks something: three ways back, from smallest to largest",
            "Most regressions are a single package or a new kernel; both can be undone on the host in minutes. Anything worse goes back to the recovery point.",
            height=600, accent=C.red, vendor="Red Hat")

opts = [("A", C.green, "A package regressed", ["dnf history list", "dnf history info <id>", "dnf history undo <id>"], "Needs the old versions still in the repositories"),
        ("B", C.gold, "The new kernel regressed", ["Pick the previous kernel in GRUB", "grubby --set-default /boot/vmlinuz-<old>", "installonly_limit=3 keeps three kernels"], "Needs console access for the GRUB menu"),
        ("C", C.red, "Anything worse", ["Restore the recovery point or snapshot", "taken before the window", "then re-plan the change"], "Needs the backup the prerequisites asked for")]
for i, (l, col, t, b, need) in enumerate(opts):
    x = 32 + i * 412
    d.card(x, 110, 392, 180, t, b, badge=l, badge_color=col, accent=col, mono_body=(i < 2))
    d.card(x, 306, 392, 64, "Precondition", [need], icon="info-card", shadow=False)

d.zone(32, 396, 1216, 130, "Kernel CVEs between windows: live patching", icon="lightning")
d.card(48, 436, 580, 72, "dnf install kpatch-dnf && dnf kpatch auto", ["Fixes selected critical and important kernel CVEs in the running kernel"], icon="terminal-blue", accent=C.blue)
d.card(652, 436, 580, 72, "Still reboot in the next window", ["Live patches cover only supported kernel releases and selected CVEs"], icon="refresh-green", accent=C.gold)
d.note_bottom("Record the dnf transaction ID with the change; it is the rollback handle. Controls supported: CP-10, CM-3, SI-2.")
d.render(repo_path("linux-administration/diagrams/sop-lnx-002-2.svg"))
