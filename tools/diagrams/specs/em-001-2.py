import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Seven profiles, what each unlocks on the Mac, and what breaks without it",
            "Each signed profile pre-approves one macOS permission; the onboarding profile ties the agent to the tenant; the app lands last so nobody is prompted.",
            height=800)

# ---------------- delivery order
d.zone(32, 100, 1216, 128, "Delivery order: profiles first, app last", icon="checklist-purple",
       note="all eight profiles: Templates › Custom, Device channel, assigned to the dynamic Mac group")
d.card(48, 142, 330, 72, "Seven permission profiles", ["one custom profile per .mobileconfig file, named macOS - Defender - <purpose>"],
       badge="1", accent=C.blue)
d.arrow([(378, 178), (420, 178)], C.blue)
d.card(422, 142, 330, 72, "Onboarding profile (the eighth)", ["WindowsDefenderATPOnboarding.xml from the Defender portal; tenant-specific"],
       badge="2", accent=C.purple)
d.arrow([(752, 178), (794, 178)], C.purple)
d.card(796, 142, 436, 72, "App assigned as Required", ["Microsoft Defender for Endpoint (macOS); Available would make it optional"],
       badge="3", accent=C.green, pill=("Required", C.green))

# ---------------- the seven profiles
d.zone(32, 244, 1216, 362, "The seven permission profiles", icon="apple", note="download each with Download raw file; the folder page saves as HTML")
rows = [["Profile file", "Grants on the Mac", "Defender capability it unlocks", "Without the profile"],
        ["fulldisk.mobileconfig", "Full Disk Access", "Real-time protection, scanning", "No file access for real-time protection and scanning"],
        ["sysext.mobileconfig", "System extension approval", "EDR telemetry", "The user is asked to approve the extension (app landed first)"],
        ["netfilter.mobileconfig", "Network content filter", "Network protection", "Network protection has no filter to attach to"],
        ["background_services.mobileconfig", "Background task approval", "Silent operation", "The agent cannot run in the background unprompted"],
        ["notif.mobileconfig", "Notifications", "User alerts", "Users never see a Defender alert"],
        ["accessibility.mobileconfig", "Accessibility", "Endpoint DLP", "Endpoint DLP cannot observe user actions"],
        ["bluetooth.mobileconfig", "Bluetooth", "Device control", "Device control cannot govern Bluetooth"]]
y_end = d.table(48, 286, [262, 214, 246, 462], rows, row_h=34, size=11.5, mono_cols=(0,), col_colors=[C.blue, C.ink, C.ink, C.grey])
d.text(48, y_end + 20, "Skip kext.mobileconfig: it is the legacy kernel-extension profile and is not needed on macOS 13 or later.", 11.5, 400, C.grey)

# ---------------- failure modes
d.callout(32, 622, 392, 108, "Profile shows Error", kind="warn",
          body=["An HTML page was saved instead of the raw profile, or the profile went out on the User channel instead of the Device channel."])
d.callout(444, 622, 392, 108, "User asked to approve the system extension", kind="note",
          body=["The sysext profile arrived after the app. Check that device ownership is Corporate and the profile assignment reached the group."])
d.callout(856, 622, 392, 108, "Why ownership must be Corporate", kind="info",
          body=["Personal-owned devices can prompt the user to approve extensions and permissions even when the profiles are present."])

d.note_bottom("7 permission profiles + 1 onboarding profile = 8 profiles Succeeded per Mac; 1 app Required. Controls: CM-2, CM-6 (managed configuration), SI-3, SI-4.")
d.render(repo_path("endpoint-management/diagrams/sop-em-001-2.svg"))
