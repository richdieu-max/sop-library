import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Classifying a change: class, GxP impact and risk decide the path",
            "Three questions in order: is it pre-approved, could it touch GxP records or a validated function, and how deep must the testing go; the answers set the approvals and the evidence.",
            height=760)

# ---------------- 1. class
d.zone(32, 100, 392, 262, "1 · Which class is it?", icon="hierarchy")
d.card(48, 140, 360, 66, "Standard", ["pre-approved, low-risk, repeatable, with a documented procedure"], badge="S", badge_color=C.green, accent=C.green, shadow=False, body_size=11, pill=("logged per instance", C.green))
d.card(48, 214, 360, 66, "Normal", ["anything not pre-approved: OS upgrade, instrument driver, static IP change, agent install"], badge="N", badge_color=C.blue, accent=C.blue, shadow=False, body_size=11, pill=("full chain", C.blue))
d.card(48, 288, 360, 66, "Emergency", ["restore service now, or close an actively exploited risk"], badge="E", badge_color=C.red, accent=C.red, shadow=False, body_size=11, pill=("retrospective QA", C.red))

# ---------------- 2. GxP impact screen
d.zone(444, 100, 392, 262, "2 · GxP impact: five questions, all answered", icon="question-diamond")
qs = ["Creates, modifies, stores, transmits or reports GxP records?",
      "Could affect their accuracy, completeness or availability, audit trails included?",
      "Could affect a validated function?",
      "Changes security, access, e-signatures, time sync or backups?",
      "Changes the OS, a driver or firmware under the validated application?"]
yy = 140
for i, q in enumerate(qs):
    d.badge(466, yy + 11, str(i + 1), C.purple, r=9, size=10)
    yy = d.lines(482, yy + 15, q, 11, 330, 400, C.ink, lh=14) + 6
d.pill(460, 334, "any Yes = GxP impact: QA signs", C.purple)
d.pill(690, 334, "all No: rationale recorded", C.grey)

# ---------------- 3. risk rating -> test depth
d.zone(856, 100, 392, 262, "3 · Risk sets the test depth", icon="target")
d.card(872, 140, 360, 62, "High", ["scripted, pre-approved steps, independently executed and signed"], accent=C.red, shadow=False, body_size=11, pill=("scripted", C.red))
d.card(872, 210, 360, 62, "Medium", ["scripted for critical functions, exploratory for the rest"], accent=C.gold, shadow=False, body_size=11, pill=("mixed", C.gold))
d.card(872, 280, 360, 62, "Low", ["unscripted or leveraged vendor evidence, summarised with outcome"], accent=C.green, shadow=False, body_size=11, pill=("summarised", C.green))
d.text(872, 354, "Severity × likelihood, adjusted by detectability; rationale agreed with QA", 10.5, 400, C.grey, max_w=364)

# ---------------- resulting path matrix
d.zone(32, 384, 1216, 302, "What the answers produce: approvals and evidence by class", icon="checklist-purple")
cols = [(48, 150, "Class"), (206, 380, "Approval chain"), (594, 320, "Evidence the record must carry"), (922, 310, "If GxP impact is Yes")]
hy = 442
d.rect(48, hy - 18, 1184, 26, fill=C.zone, stroke=C.border, rx=4)
for x, w, label in cols:
    d.text(x + 8, hy, label, 11.5, 600, C.ink)
rows = [
    ("Standard", C.green, "CAB and QA approve the procedure once; each instance is logged against it",
     "instance log entry; the pre-approved procedure reference; evidence named in that procedure",
     "stays Standard only while identical; a difference re-routes it as Normal"),
    ("Normal", C.blue, "change owner › system owner › CAB › QA, each a signed step, before the window opens",
     "plan with numbered steps and expected results; baseline; test scripts traced to requirements; tested rollback",
     "QA electronic signature required; IQ, OQ and PQ evidence as planned"),
    ("Emergency", C.red, "emergency CAB, expedited; who authorized it, when and how, logged as it happens",
     "what baseline could be taken; every action with a time; record raised the same day, linked to the incident",
     "retrospective impact assessment, verification, CAB and QA approval, PIR; a refusal becomes a deviation"),
]
y = 460
for name, col, chain, ev, gxp in rows:
    d.card(48, y, 1184, 64, "", [], accent=col, shadow=False)
    d.text(66, y + 36, name, 13.5, 600, col)
    d.lines(214, y + 18, chain, 11, 362, 400, C.ink, lh=14)
    d.lines(602, y + 18, ev, 11, 304, 400, C.ink, lh=14)
    d.lines(930, y + 18, gxp, 11, 296, 400, C.ink, lh=14)
    y += 72

d.note_bottom("Segregation of duties: the implementer is not the only approver and never approves their own test results. Controls: CM-3, CM-4, CM-5, SA-10; 21 CFR Part 11 §11.10(a), (k); Annex 11 change management.")
d.render(repo_path("governance/diagrams/sop-gov-001-2.svg"))
