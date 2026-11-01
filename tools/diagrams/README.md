# Diagram renderer

Every figure added since the concept-diagram set is generated from a short Python spec, so a figure can be
corrected, re-styled or reproduced without a drawing tool. `build.py` renders every spec into the runbooks'
`diagrams/` folders; the workflow in `.github/workflows/diagrams.yml` rebuilds them on every push and fails
if the committed SVG drifts from its spec.

```bash
python3 tools/diagrams/build.py            # all figures (needs only the standard library)
python3 tools/diagrams/build.py az-102-2   # one figure
```

The 54 figures from the first edition predate the renderer and have no spec; they share the same palette,
icon set and footer.

## How a spec reads

```python
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from kit import Diagram, C, repo_path

d = Diagram("Title", "One-sentence subtitle.", height=760)
d.zone(32, 100, 600, 300, "Zone heading", icon="users", note="right-aligned note")
d.card(52, 144, 260, 66, "Card title", ["body text wraps automatically"], icon="user", accent=C.blue, pill=("read", C.green))
d.arrow([(312, 177), (376, 177)], C.blue, label="then")
d.note_bottom("Numbers and control references.")
d.render(repo_path("family-folder/diagrams/sop-xx-nnn-n.svg"))
```

`kit.py` provides zones, cards, arrows, pills, badges, chips, callouts, tables, status cells, sequence
diagrams and timelines, plus the icon library in `icons.json` (`kit.icon_names()` lists it). Text is wrapped
with an approximate Segoe UI metric and anything that would overflow its box is reported as a warning, which
`build.py` treats as a failure.

## House rules the kit assumes

- 1280 wide; title at 22px, subtitle at 13.5px, body never below 10.5px; content ends above the footer rule.
- Status pills instead of colour-only coding; numbered badges for steps, letters for alternatives.
- Orthogonal arrows; five to twelve cards per figure; one footnote line with the numbers and control references.
- No client names, tenant IDs, real hostnames or addresses: placeholders are Contoso, `<tenant-id>`,
  `PC-LAB-0001`, and RFC 5737 ranges such as 192.0.2.0/24.
- Icons are simplified originals, not Microsoft artwork.
