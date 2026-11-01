import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Anatomy of one crosswalk row: one control, one receipt, five departments",
            "LOG-01 from the template, exploded: the control is the purchase, the hashed evidence file is the receipt, and each framework column is a department that files the same receipt.",
            height=800)

# ---- the row, left to right
d.zone(32, 100, 1216, 250, "SOP-08-crosswalk.template.csv · row LOG-01", icon="list-blue", note="one row per built control, never one per framework")
d.card(46, 140, 176, 96, "Control ID (internal)", ["LOG-01"], accent=C.blue, shadow=False, title_size=12, body_size=12, mono_body=True)
d.card(234, 140, 236, 96, "Control statement", ["Activity log streamed to central workspace"], accent=C.blue, shadow=False, title_size=12, body_size=11.5)
d.card(482, 140, 236, 96, "Azure implementation", ["activity-to-law diagnostic setting (the exact setting, not a product name)"], accent=C.purple, shadow=False, title_size=12, body_size=11.5)
d.card(730, 140, 236, 96, "Evidence file", ["diag-settings.json, listed in MANIFEST.csv with its SHA-256"], accent=C.green, shadow=False, title_size=12, body_size=11.5, pill=("hashed", C.green))
d.card(978, 140, 256, 96, "Status", ["Built: the export shows it in place. A non-compliant row goes to the risk register, never a footnote"], accent=C.gold, shadow=False, title_size=12, body_size=11.5, pill=("Built", C.green))
for x in (222, 470, 718, 966):
    d.arrow([(x, 188), (x + 12, 188)], C.grey, sw=1.5)
d.text(46, 262, "The five framework columns on the same row", 12, 600, C.ink)
fw = [("NIST CSF 2.0", "DE.CM-09", "outcome, from the framework text", C.blue),
      ("NIST SP 800-53 R5", "AU-2 / AU-6", "control, from the initiative group", C.purple),
      ("ISO/IEC 27001:2022", "A.8.15", "Annex A control, from the initiative group", C.teal),
      ("HIPAA Security Rule", "164.312(b)", "safeguard, from the HITRUST/HIPAA initiative", C.gold),
      ("PCI DSS v4 (boundary)", "10.2.1", "requirement, boundary only, from the attestation letter", C.red)]
for i, (name, ref, src, col) in enumerate(fw):
    x = 46 + i * 240
    d.card(x, 272, 228, 66, name, [src], accent=col, shadow=False, title_size=11.5, body_size=10.5)
    d.text(x + 222, 294, ref, 12, 600, col, "end", mono=True)

# ---- two more rows, compact, to show the shape holds
d.zone(32, 370, 740, 190, "Two more rows from the template, same shape", icon="checklist-purple")
d.table(46, 410, [70, 218, 70, 60, 58, 112, 60, 64], [
    ["ID", "Statement", "CSF 2.0", "800-53", "ISO", "HIPAA", "PCI", "Status"],
    ["NET-01", "No public IPs on network interfaces", "PR.IR-01", "SC-7", "A.8.20", "164.312(e)(1)", "1.3.1", "Built"],
    ["BAK-01", "Backups geo-redundant to paired region", "PR.DS-11", "CP-9", "A.8.13", "164.308(a)(7)(ii)(A)", "N/A", "Built"],
], row_h=26, size=10.5, mono_cols=(0,))
d.text(46, 508, "NET-01 is proven by deny-nic-public-ip in policy-compliance.csv; BAK-01 by rsv-config.json. PCI is N/A where the", 10.5, 400, C.grey)
d.text(46, 524, "boundary does not reach: card data never touches the tenant, so most rows carry no PCI requirement at all.", 10.5, 400, C.grey)

# ---- rules
d.zone(792, 370, 456, 190, "Rules that keep the crosswalk honest", icon="shield-check")
d.card(806, 410, 428, 44, "Map only what is built", ["a row for a control the build does not implement fails at the first sample"], accent=C.red, shadow=False, title_size=12, body_size=10.5)
d.card(806, 460, 428, 44, "Name the setting and the file", ["a mapping by name only is what an auditor rejects"], accent=C.gold, shadow=False, title_size=12, body_size=10.5)
d.card(806, 510, 428, 44, "Same scope, same day", ["Policy and Defender exports taken together, or their numbers disagree"], accent=C.blue, shadow=False, title_size=12, body_size=10.5)

# ---- where the evidence comes from
d.zone(32, 580, 1216, 140, "Where the receipts come from", icon="hash-doc")
srcs = [("Policy › Compliance export", "SOP-08-compliance-export.ps1: one CSV per initiative with its control groups, plus 01-summary-by-initiative.csv", C.purple),
        ("Defender regulatory compliance", "NIST SP 800-53 R5, ISO 27001, HIPAA HITRUST and PCI DSS v4 added as standards; Download report for each", C.blue),
        ("MANIFEST.csv", "SHA-256 of every export; the crosswalk references the manifest version, so a changed file is visible", C.green),
        ("PCI boundary letter", "states card data is handled by the processor and lists the controls that keep it that way; signed by the client approver", C.red)]
for i, (t, b, col) in enumerate(srcs):
    d.card(46 + i * 302, 620, 290, 88, t, [b], accent=col, shadow=False, title_size=12, body_size=10.5)

d.note_bottom("Verify: every row names an evidence file in the manifest; non-compliant counts match the risk register; the PCI letter is signed. Controls: CA-2, CA-7, PL-2; ISO 6.1.3, 9.2; PCI 12.5.2.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-108-2.svg"))
