import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Life of a finding: from scanner output to a closed, hashed record",
            "Three scanners feed one triage; a real secret is rotated before anyone reads the report, a CVE gets an owner and a date, and every output is hashed before it is opened.",
            height=800)

# ---- scanners (left column)
d.zone(32, 100, 300, 356, "Scanners", icon="doc-search", note="full history, not just the branch")
d.card(46, 140, 272, 96, "gitleaks", ["keys, tokens, passwords and connection strings in every commit of every branch; output is file, commit and rule, values redacted"], icon="git-branch", accent=C.red, shadow=False, body_size=11)
d.card(46, 244, 272, 96, "Trivy", ["CVEs, secrets and misconfiguration in files, IaC and the deployed image, CRITICAL and HIGH; plus a CycloneDX SBOM"], icon="package", accent=C.gold, shadow=False, body_size=11)
d.card(46, 348, 272, 96, "Dependabot", ["known-vulnerable dependencies, continuously; open alerts exported with a token scoped to the one repository"], icon="bell", accent=C.purple, shadow=False, body_size=11)
for yy in (188, 292, 396):
    d.arrow([(318, yy), (360, yy), (360, 278), (382, 278)], C.grey, sw=1.5)

# ---- triage (middle)
d.zone(384, 100, 466, 356, "Triage: every hit gets exactly one outcome", icon="question-diamond-gold")
d.card(398, 140, 438, 54, "Is the secret hit real?", ["real secret · test value · false positive, decided per hit"], badge="1", accent=C.gold, shadow=False, title_size=12.5, body_size=11)
d.card(398, 202, 212, 100, "Real secret", ["rotate it in the vault, then purge the history; record file, commit and rule only, never the value"], accent=C.red, shadow=False, title_size=12.5, body_size=11, pill=("rotate", C.red))
d.card(622, 202, 214, 100, "Not a real secret", ["record the triage result beside the hit so the next scan does not reopen it"], accent=C.grey, shadow=False, title_size=12.5, body_size=11, pill=("record", C.grey))
d.card(398, 310, 438, 130, "CVE or misconfiguration", ["CRITICAL: no row may remain without an accepted-risk ID. Every CVE gets a fix path: owner role and target date. Counts are reported by severity"], badge="2", accent=C.gold, shadow=False, title_size=12.5, body_size=11, pill=("fix path", C.gold))
d.arrow([(836, 278), (880, 278)], C.grey, sw=1.5)

# ---- close-out (right)
d.zone(882, 100, 366, 356, "Close-out", icon="hash-doc")
d.card(896, 140, 338, 84, "Hash before anyone reads", ["sha256sum of every output into MANIFEST.sha256 in the run folder; delivered files must match the manifest"], badge="3", accent=C.green, shadow=False, title_size=12.5, body_size=11)
d.card(896, 232, 338, 84, "Rotate before the report ships", ["a report that contains a secret has just leaked it again: reference the commit and rule, and rotate first"], badge="4", accent=C.red, shadow=False, title_size=12.5, body_size=11)
d.card(896, 324, 338, 118, "Report", ["counts by severity, the triage result for each secret hit, the fix path for each CVE; non-compliant items go to the risk register"], badge="5", accent=C.blue, shadow=False, title_size=12.5, body_size=11)

# ---- bottom side panels
d.zone(32, 476, 400, 250, "Before the first scan", icon="certificate", fill=C.goldtint, stroke=C.gold, title_color=C.gold, dashed=True)
d.lines(46, 518, "Written authorization on file naming the repository the client treats as canonical, and the dates. Never a fork or a developer copy; the owner confirms which repository is canonical.", 11.5, 372, 400, C.grey)
d.lines(46, 600, "Clone with git clone --mirror so every branch and every old commit is in scope: a shallow clone finds nothing in an old repository.", 11.5, 372, 400, C.grey)
d.pill(46, 688, "gitleaks 8.x", C.gold); d.pill(150, 688, "Trivy 0.5x", C.gold); d.pill(240, 688, "run ID per evidence folder", C.gold)

d.zone(452, 476, 390, 250, "Licence inventory", icon="list-blue")
d.lines(466, 518, "Trivy writes a CycloneDX SBOM (sbom.cdx.json) from the same clone. It lists every component and its licence, so the inventory comes from what is actually built, not from a spreadsheet kept by hand.", 11.5, 362, 400, C.grey)
d.card(466, 610, 362, 100, "Where it lands", ["sbom.cdx.json in the run folder, hashed into the manifest; dependency and supply-chain rows reference it"], accent=C.blue, shadow=False, title_size=12.5, body_size=11, pill=("SA-15, SR-3", C.blue))

d.zone(862, 476, 386, 250, "The vault stays private: prove it twice", icon="lock")
d.table(876, 514, [164, 120], [["Check (read-only)", "Expect"], ["RBAC mode", "True"], ["Purge protection", "True"], ["Public network access", "Disabled"], ["IP rules", "0"], ["Private endpoint", "Approved"]], row_h=24, size=11)
d.lines(876, 672, "Then from outside the private network open Objects › Secrets: the portal must refuse to list them. That refusal is the evidence that a stolen portal session alone cannot read a secret.", 11, 356, 400, C.ink)

d.note_bottom("Verify: manifest hashes match; every gitleaks hit has a triage result and every real secret a rotation record; no CRITICAL Trivy row without an accepted-risk ID. Controls: IA-5(7), RA-5, SA-15, SR-3, SC-12.")
d.render(repo_path("azure-landing-zone-series/diagrams/sop-az-105-2.svg"))
