"""Dark theme for the diagram set.

The figures are drawn in a light Fluent palette and then mapped onto a dark palette that sits on
GitHub's dark canvas (#0D1117). The mapping is context-aware:

- the full-size background becomes the canvas, white cards and table rows become raised surfaces,
  and the white label masks on arrows become the canvas colour;
- accent colours used for text, strokes and arrow heads get a brighter tone so they stay readable;
  accent colours used as solid fills (badges, pills, accent bars) get a mid tone so white text on
  them keeps its contrast;
- pale tints (zone and pill backgrounds) become deep tints of the same hue;
- icon groups (`<g transform="... scale(...)">`) are left exactly as drawn.

`to_dark()` is idempotent on output it produced: every source colour it maps is a light-palette
colour, and none of the dark colours it writes is a source colour.
"""

import re

CANVAS = "#0D1117"
ZONE = "#151B23"
CARD = "#1C2128"

# Neutrals: same tone for every context.
NEUTRAL = {
    "#201F1E": "#E6EDF3",  # ink
    "#605E5C": "#9198A1",  # grey ink, secondary arrows
    "#8A8886": "#7D8590",  # light ink, connectors
    "#C8C6C4": "#3D444D",  # card border
    "#E1DFDD": "#30363D",  # rules, row borders
    "#FAF9F8": ZONE,       # zone fill
    "#F3F2F1": ZONE,
    "#FCFCFB": "#181E26",  # zebra row
    "#2D4552": "#2D4552",
}

# Accents: (bright tone for text / strokes / arrow heads, mid tone for solid fills).
ACCENT = {
    "#0078D4": ("#4493F8", "#1F6FEB"),  # blue
    "#005A9E": ("#79C0FF", "#1158C7"),  # dark blue
    "#107C10": ("#3FB950", "#238636"),  # green
    "#A4262C": ("#F85149", "#DA3633"),  # red
    "#C19C00": ("#D29922", "#9E6A03"),  # gold
    "#8A6D00": ("#E3B341", "#9E6A03"),
    "#7A5F00": ("#E3B341", "#9E6A03"),
    "#7A6200": ("#E3B341", "#9E6A03"),
    "#5C2D91": ("#A371F7", "#8957E5"),  # purple
    "#008272": ("#39C5CF", "#1B7C83"),  # teal
    "#008575": ("#39C5CF", "#1B7C83"),
}

# Pale tints used as zone, pill and callout backgrounds.
TINT = {
    "#F3F9FD": "#121D2F", "#EFF6FC": "#121D2F", "#DEECF9": "#1A2E4A",
    "#FFF8F8": "#25171C", "#FDE7E9": "#3A1D22",
    "#FFFCF0": "#211D12", "#FFF9E6": "#272115", "#FFF4CE": "#33290F",
    "#F6FBF6": "#13201A", "#F2FAF2": "#15221A", "#DFF6DD": "#1B3222",
    "#FAF6FD": "#1E182C", "#F6F2FA": "#221A32", "#EFE6F7": "#2A1F3D",
    "#EEF8F6": "#12231F", "#D9F2EF": "#13302E",
}

_TAG = re.compile(r"<(/?)([a-zA-Z]+)([^>]*?)(/?)>")
_COLOR = re.compile(r'(fill|stroke|stop-color)="(#[0-9A-Fa-f]{3,6}|white)"')


def _norm(c):
    c = c.upper()
    if c == "WHITE":
        return "#FFF"
    if c == "#FFFFFF":
        return "#FFF"
    return c


def _map(attr, colour, tag, attrs, in_marker):
    c = _norm(colour)
    if c == "#FFF":
        if tag == "text" or tag == "tspan":
            return colour  # white text on a solid badge or pill
        if tag == "rect" and " x=" not in " " + attrs and "width=" in attrs:
            return CANVAS  # the full-size background
        if 'opacity="' in attrs:
            return CANVAS  # label masks over arrows
        if tag == "rect" and 'height="6"' in attrs:
            return CANVAS
        return CARD  # cards, table rows, badge halos
    if c == "#000":
        return colour  # card shadows
    if c in NEUTRAL:
        return NEUTRAL[c]
    if c in TINT:
        return TINT[c]
    if c in ACCENT:
        bright, mid = ACCENT[c]
        if in_marker or attr == "stroke" or tag in ("text", "tspan"):
            return bright
        return mid
    return colour


def to_dark(svg):
    out = []
    pos = 0
    stack = []  # (tag, inside_icon, inside_marker)
    for m in _TAG.finditer(svg):
        close, tag, attrs, selfclose = m.groups()
        out.append(svg[pos:m.start()])
        pos = m.end()
        if close:
            if stack:
                stack.pop()
            out.append(m.group(0))
            continue
        parent_icon = bool(stack) and stack[-1][1]
        parent_marker = bool(stack) and stack[-1][2]
        icon = parent_icon or (tag == "g" and "scale(" in attrs)
        marker = parent_marker or tag == "marker"
        if icon:
            new_attrs = attrs
        else:
            new_attrs = _COLOR.sub(lambda a: f'{a.group(1)}="{_map(a.group(1), a.group(2), tag, attrs, marker)}"', attrs)
        out.append(f"<{close}{tag}{new_attrs}{selfclose}>")
        if not selfclose and not tag.startswith("?") and not tag.startswith("!"):
            stack.append((tag, icon, marker))
    out.append(svg[pos:])
    return "".join(out)


if __name__ == "__main__":
    import sys

    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        dst = to_dark(src)
        if dst != src:
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(dst)
            print("dark:", path)
