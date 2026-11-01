import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("What a compatibility shim changes for the application, and how it is applied at scale",
            "The shim sits between the legacy executable and Windows 11: it answers the version check and redirects the writes the app expects to make, while the OS itself stays unchanged.",
            height=700)

# ---------------- left: where the shim sits
d.zone(32, 100, 600, 424, "Where the shim sits", icon="merge-purple", note="applied per executable, loaded at process start")
d.card(52, 146, 560, 66, "Legacy instrument application",
       ["built for Windows 7: checks the OS version, writes beside its own files and under HKLM"],
       icon="app-window", accent=C.gold)
d.arrow([(332, 212), (332, 238)], C.gold)
d.zone(52, 240, 560, 170, "Compatibility layer", icon="gear", fill=C.paper, note="Windows 7 mode plus the specific fixes the app needs")
d.card(66, 282, 172, 112, "WIN7RTM mode", ["version check: the app is told it runs on Windows 7, so the check passes"],
       accent=C.blue, shadow=False, title_size=12.5, body_size=11)
d.card(250, 282, 172, 112, "CorrectFilePaths", ["file writes: writes aimed at Program Files go to a path a standard user may use"],
       accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.card(434, 282, 172, 112, "VirtualRegistry", ["registry writes: HKLM writes the app expects are virtualized for a standard user"],
       accent=C.purple, shadow=False, title_size=12.5, body_size=11)
d.arrow([(332, 410), (332, 436)], C.blue)
d.card(52, 438, 560, 66, "Windows 11 Enterprise, fully patched",
       ["sees ordinary calls; nothing in the OS is changed. The shim is configuration: reviewed, versioned, in the IQ"],
       icon="windows", accent=C.blue)

# ---------------- right: two ways to apply, one way to deploy
d.zone(656, 100, 592, 424, "Two ways to apply it, one way to deploy it", icon="package", note="letters are alternatives")
d.card(672, 146, 276, 150, "Layer value, all users",
       ["HKLM › SOFTWARE › Microsoft › Windows NT › CurrentVersion › AppCompatFlags › Layers",
        "value name = full path to the .exe; data = ~ WIN7RTM",
        "one mode flag, no specific fixes"],
       icon="list-blue", accent=C.blue, badge="A", badge_color=C.blue)
d.card(956, 146, 276, 150, "Custom shim database (.sdb)",
       ["Compatibility Administrator from the Windows ADK; 32-bit edition for 32-bit apps",
        "Windows 7 mode plus CorrectFilePaths or VirtualRegistry; tested, then saved as <app>-Win11.sdb"],
       icon="doc-check-purple", accent=C.purple, badge="B", badge_color=C.purple)
d.arrow([(1094, 296), (1094, 330)], C.purple)
d.card(672, 332, 560, 76, "Deploy at scale: sdbinst.exe -q in Intune or ConfigMgr",
       ["the .sdb is versioned, referenced in the IQ and re-tested whenever the application or OS version changes"],
       icon="devices", accent=C.green)
d.card(672, 424, 560, 76, "Rollback",
       ["Remove-ItemProperty the Layers value, or sdbinst -u the database; the untouched reference PC stays in service until OQ passes"],
       icon="refresh-green", accent=C.grey)

# ---------------- bottom: cautions and validation
d.callout(32, 540, 600, 84, "Avoid RUNASADMIN", kind="warn",
          body=["Use it only if the vendor requires it, and record it in the risk assessment. Per-user compatibility settings are for first launch; production uses the all-users layer or the .sdb."])
d.callout(656, 540, 592, 84, "Validation footprint", kind="ok",
          body=["Posture as Method A (fully patched) with the shim reviewed; IQ/OQ of the platform plus the shim as configuration; re-test per application or OS update."])

d.note_bottom("Symptoms it answers: 'unsupported OS' at install (version check); works for admins but not operators (writes to Program Files or HKLM). Controls: Part 11 §11.10(a); Annex 11 configuration management.")
d.render(repo_path("regulated-lab-it/diagrams/sop-lab-001-4.svg"))
