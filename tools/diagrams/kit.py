"""Diagram kit: renders the SOP library figures (1280 wide, Fluent palette, Segoe UI stack, shadowed cards
with 4px accent, 48-unit icons, per-colour arrow markers, fixed footer). Specs live in specs/; build.py runs them all.

Usage
-----
    from kit import Diagram, C
    d = Diagram("Title", "Subtitle sentence.", height=760)
    d.zone(32, 100, 400, 300, "Zone title", icon="users", note="right note")
    d.card(52, 144, 260, 66, "Card title", ["body line 1", "body line 2"], icon="user", accent=C.blue)
    d.arrow([(312, 177), (376, 177)], C.blue)
    d.render("out.svg")   # prints overflow warnings; returns list of warnings

Coordinates are absolute, in the 1280-wide canvas. Content starts at y=100 (title at 48,
subtitle at 72). The footer needs 70px: keep content above height-70.
"""
import json
import os
import re
import html as _html

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))


def repo_path(rel):
    """Absolute path of a file inside the repository, from a path relative to its root."""
    return os.path.join(REPO_ROOT, rel)

FONT = "'Segoe UI', 'Segoe UI Web', -apple-system, BlinkMacSystemFont, 'Helvetica Neue', Arial, sans-serif"
MONO = "Consolas, 'Cascadia Mono', Menlo, monospace"


class C:
    """Fluent palette used by the existing diagrams."""
    paper = "#fff"
    ink = "#201F1E"
    grey = "#605E5C"
    light = "#8A8886"
    border = "#C8C6C4"
    rule = "#E1DFDD"
    zone = "#FAF9F8"
    blue = "#0078D4"
    darkblue = "#005A9E"
    purple = "#5C2D91"
    gold = "#C19C00"
    green = "#107C10"
    red = "#A4262C"
    teal = "#008272"
    redtint = "#FFF8F8"
    goldtint = "#FFF9E6"
    greentint = "#F2FAF2"
    bluetint = "#EFF6FC"
    purpletint = "#F6F2FA"
    tealtint = "#EEF8F6"


TINT = {C.blue: C.bluetint, C.red: C.redtint, C.gold: C.goldtint, C.green: C.greentint,
        C.purple: C.purpletint, C.teal: C.tealtint, C.grey: C.zone, C.darkblue: C.bluetint, C.ink: C.zone}

# ------------------------------------------------------------------ icons
with open(os.path.join(HERE, "icons.json"), encoding="utf-8") as fh:
    ICONS = json.load(fh)


def icon_names():
    return sorted(ICONS)


# ------------------------------------------------------------------ text metrics (approximate Segoe UI / Helvetica)
_W = {}
for ch in "iljtfI.,:;'|!()[]{}/\\ ": _W[ch] = 0.30
for ch in "r": _W[ch] = 0.36
for ch in "abcdeghknopqsuvxyz": _W[ch] = 0.54
for ch in "mw": _W[ch] = 0.82
for ch in "ABCDEFGHJKLNOPQRSTUVXYZ": _W[ch] = 0.66
for ch in "MW": _W[ch] = 0.88
for ch in "0123456789": _W[ch] = 0.56
_W[" "] = 0.29
for ch in "-–·": _W[ch] = 0.36
for ch in "—": _W[ch] = 0.9
for ch in "+=<>~^*#%&@$": _W[ch] = 0.62
for ch in "→←↑↓↔": _W[ch] = 0.9
for ch in "›": _W[ch] = 0.36
for ch in " ": _W[ch] = 0.29


def text_width(s, size, weight=400):
    w = sum(_W.get(c, 0.6) for c in s) * size
    if weight >= 600:
        w *= 1.06
    return w * 1.04  # safety margin for font substitution


def wrap(s, size, max_w, weight=400, max_lines=None):
    words = s.split(" ")
    lines, cur = [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if text_width(t, size, weight) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    if max_lines and len(lines) > max_lines:
        raise ValueError(f"text needs {len(lines)} lines (> {max_lines}): {s!r}")
    return lines


def esc(s):
    return _html.escape(str(s), quote=True)


# ------------------------------------------------------------------ diagram
class Diagram:
    def __init__(self, title, subtitle, height=760, accent=C.blue, aria=None):
        self.title, self.subtitle, self.h, self.accent = title, subtitle, height, accent
        self.aria = aria or title
        self.parts, self.markers, self.warnings = [], {}, []
        self.min_bottom = 100
        self._check_text(title, 22, 1216, 600, "title")
        self._check_text(subtitle, 13.5, 1216, 400, "subtitle")

    # ---------------- helpers
    def _check_text(self, s, size, max_w, weight, where):
        w = text_width(s, size, weight)
        if w > max_w:
            self.warnings.append(f"OVERFLOW {where}: {w:.0f}px > {max_w}px: {s[:60]!r}")

    def _marker(self, color, start=False):
        mid = "m" + color.lstrip("#") + ("s" if start else "")
        if mid not in self.markers:
            if start:
                self.markers[mid] = (f'<marker id="{mid}" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="8" markerHeight="8" '
                                     f'orient="auto"><path d="M10,0 L0,5 L10,10 z" fill="{color}"/></marker>')
            else:
                self.markers[mid] = (f'<marker id="{mid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" '
                                     f'orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker>')
        return mid

    def _touch(self, y):
        self.min_bottom = max(self.min_bottom, y)

    # ---------------- primitives
    def text(self, x, y, s, size=12, weight=400, color=None, anchor="start", mono=False, max_w=None, italic=False):
        color = color or (C.ink if weight >= 600 else C.grey)
        if max_w:
            self._check_text(s, size, max_w, weight, f"text@({x},{y})")
        style = f' font-style="italic"' if italic else ""
        self.parts.append(f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONT}" font-size="{size}" '
                          f'font-weight="{weight}" fill="{color}" text-anchor="{anchor}"{style}>{esc(s)}</text>')
        self._touch(y + 4)

    def lines(self, x, y, s, size=12, max_w=300, weight=400, color=None, lh=None, anchor="start", max_lines=None, mono=False):
        """Wrapped paragraph. Returns y after the last line."""
        lh = lh or round(size * 1.4)
        ls = wrap(s, size, max_w, weight, max_lines) if not mono else [s]
        for i, line in enumerate(ls):
            self.text(x, y + i * lh, line, size, weight, color, anchor, mono=mono)
        return y + len(ls) * lh

    def icon(self, x, y, name, scale=0.5, color=None):
        inner = ICONS[name]
        if color:
            inner = re.sub(r'fill="#(?!fff)[0-9A-Fa-f]{6}"', f'fill="{color}"', inner)
        self.parts.append(f'<g transform="translate({x},{y}) scale({scale:.4f})">{inner}</g>')

    def rect(self, x, y, w, h, fill=C.paper, stroke=C.border, sw=1, rx=5, dashed=False, opacity=None):
        d = ' stroke-dasharray="6 4"' if dashed else ""
        o = f' opacity="{opacity}"' if opacity is not None else ""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}{o}/>')
        self._touch(y + h)

    def zone(self, x, y, w, h, title=None, icon=None, note=None, fill=C.zone, stroke=C.border, dashed=False, title_color=None, sw=1.4):
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
                          f'{" stroke-dasharray=\"6 4\"" if dashed else ""}/>')
        tx = x + 10
        if icon:
            self.icon(x + 10, y + 8, icon, 0.5)
            tx = x + 42
        if title:
            self.text(tx, y + 25, title, 14, 600, title_color or C.ink, max_w=w - (tx - x) - (text_width(note, 11.5) + 20 if note else 12))
        if note:
            self.text(x + w - 12, y + 25, note, 11.5, 400, C.grey, "end")
        self._touch(y + h)

    def card(self, x, y, w, h, title, body=None, icon=None, accent=None, badge=None, badge_color=None, pill=None,
             shadow=True, fill=C.paper, stroke=C.border, title_size=13.5, body_size=12, mono_body=False, title_color=None):
        """Card with optional icon (left), accent bar, step badge (circle, top-left) and status pill (top-right)."""
        if shadow:
            self.parts.append(f'<rect x="{x + 1.5}" y="{y + 2}" width="{w}" height="{h}" rx="5" fill="#000" opacity="0.06"/>')
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        if accent:
            self.parts.append(f'<rect x="{x}" y="{y}" width="4" height="{h}" rx="0" fill="{accent}"/>')
        tx = x + 14 + (4 if accent else 0)
        if icon:
            self.icon(x + 12 + (4 if accent else 0), y + 10, icon, 0.5)
            tx = x + 46 + (4 if accent else 0)
        if badge is not None:
            self.badge(x + (24 if not icon else w - 20), y + 16, badge, badge_color or accent or C.blue)
            if not icon:
                tx = x + 44
        right_pad = 14
        if pill:
            pt, pc = pill
            pw = text_width(pt, 10.5, 600) + 16
            self.pill(x + w - pw - 10, y + 10, pt, pc)
            right_pad = pw + 18
        max_w = w - (tx - x) - right_pad
        self.text(tx, y + 22, title, title_size, 600, title_color or C.ink, max_w=max_w)
        yy = y + 22 + round(body_size * 1.45)
        body_w = w - (tx - x) - 12
        for para in (body or []):
            for line in ([para] if mono_body else wrap(para, body_size, body_w)):
                if yy > y + h - 3:
                    self.warnings.append(f"OVERFLOW card body: {title!r} line {line!r} below card bottom (y={yy}, bottom={y + h})")
                self.text(tx, yy, line, body_size, 400, C.grey, mono=mono_body)
                yy += round(body_size * 1.45)
        self._touch(y + h)

    def badge(self, cx, cy, label, color=C.blue, r=11, size=11):
        self.parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>')
        self.parts.append(f'<text x="{cx}" y="{cy + 4}" font-family="{FONT}" font-size="{size}" font-weight="600" fill="#fff" text-anchor="middle">{esc(label)}</text>')

    def pill(self, x, y, label, color=C.blue, solid=False, size=10.5):
        w = text_width(label, size, 600) + 16
        if solid:
            self.parts.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="20" rx="10" fill="{color}"/>')
            self.parts.append(f'<text x="{x + w / 2:.0f}" y="{y + 14}" font-family="{FONT}" font-size="{size}" font-weight="600" fill="#fff" text-anchor="middle">{esc(label)}</text>')
        else:
            self.parts.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="20" rx="10" fill="{TINT.get(color, C.zone)}" stroke="{color}" stroke-width="1"/>')
            self.parts.append(f'<text x="{x + w / 2:.0f}" y="{y + 14}" font-family="{FONT}" font-size="{size}" font-weight="600" fill="{color}" text-anchor="middle">{esc(label)}</text>')
        return w

    def chip(self, x, y, label, color=C.blue, size=11):
        """Legend chip (light tint, coloured text). Returns width."""
        w = text_width(label, size, 600) + 18
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="22" rx="11" fill="{TINT.get(color, C.bluetint)}"/>')
        self.parts.append(f'<text x="{x + w / 2:.0f}" y="{y + 15}" font-family="{FONT}" font-size="{size}" font-weight="600" fill="{color}" text-anchor="middle">{esc(label)}</text>')
        return w

    def chips(self, x, y, items, gap=8):
        for label, color in items:
            x += self.chip(x, y, label, color) + gap
        return x

    def legend(self, x, y, items, gap=26, size=11.5):
        """Coloured squares with labels in a row: items = [(label, color)]."""
        for label, color in items:
            self.parts.append(f'<rect x="{x}" y="{y - 10}" width="12" height="12" rx="2" fill="{color}"/>')
            self.text(x + 18, y, label, size, 400, C.ink)
            x += 18 + text_width(label, size) + gap
        return x

    def arrow(self, pts, color=C.blue, label=None, dashed=False, start=False, sw=2, label_size=11, label_dy=-6, label_color=None):
        """Orthogonal polyline arrow through pts; marker at the end (and start if start=True)."""
        d = ' stroke-dasharray="5 4"' if dashed else ""
        ms = f' marker-start="url(#{self._marker(color, True)})"' if start else ""
        path = " ".join(f"{p[0]},{p[1]}" for p in pts)
        self.parts.append(f'<polyline points="{path}" fill="none" stroke="{color}" stroke-width="{sw}"{d} marker-end="url(#{self._marker(color)})"{ms}/>')
        if label:
            (x1, y1), (x2, y2) = pts[0], pts[-1]
            if len(pts) >= 2:
                a, b = pts[len(pts) // 2 - 1], pts[len(pts) // 2]
                mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
            else:
                mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            w = text_width(label, label_size) + 10
            self.parts.append(f'<rect x="{mx - w / 2:.0f}" y="{my + label_dy - 11}" width="{w:.0f}" height="16" rx="3" fill="#fff" opacity="0.92"/>')
            self.text(mx, my + label_dy + 1, label, label_size, 400, label_color or color, "middle")

    def line(self, x1, y1, x2, y2, color=C.rule, sw=1, dashed=False):
        d = ' stroke-dasharray="5 4"' if dashed else ""
        self.parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{sw}"{d}/>')

    def callout(self, x, y, w, h, title, body=None, kind="note", icon=None):
        """Tinted dashed box: kind = note (gold) | warn (red) | ok (green) | info (blue)."""
        color = {"note": C.gold, "warn": C.red, "ok": C.green, "info": C.blue}[kind]
        self.zone(x, y, w, h, title, icon=icon or {"note": "info-card", "warn": "warning", "ok": "check-circle", "info": "document"}[kind],
                  fill=TINT[color], stroke=color, dashed=True, title_color=color)
        yy = y + 46
        for line in (body or []):
            yy = self.lines(x + 14, yy, line, 12, w - 28, 400, C.grey)
        if yy > y + h + 2:
            self.warnings.append(f"OVERFLOW callout {title!r}: body ends {yy:.0f} > box bottom {y + h}")
        return yy

    def table(self, x, y, col_w, rows, header=True, row_h=26, size=11.5, header_color=C.ink, zebra=True, col_colors=None, mono_cols=()):
        """Simple grid. rows = list of lists of str. Returns y after the table."""
        total_w = sum(col_w)
        yy = y
        for ri, row in enumerate(rows):
            is_h = header and ri == 0
            if is_h:
                self.parts.append(f'<rect x="{x}" y="{yy}" width="{total_w}" height="{row_h}" fill="{C.zone}" stroke="{C.border}" stroke-width="1"/>')
            else:
                fill = "#fff" if (not zebra or ri % 2 == 1) else "#FCFCFB"
                self.parts.append(f'<rect x="{x}" y="{yy}" width="{total_w}" height="{row_h}" fill="{fill}" stroke="{C.rule}" stroke-width="1"/>')
            cx = x
            for ci, cell in enumerate(row):
                color = header_color if is_h else (col_colors[ci] if col_colors and col_colors[ci] else C.grey)
                self.text(cx + 8, yy + row_h / 2 + 4, cell, size, 600 if is_h else 400, color if not is_h else header_color,
                          max_w=col_w[ci] - 14, mono=(ci in mono_cols and not is_h))
                cx += col_w[ci]
            yy += row_h
        self._touch(yy)
        return yy

    def status_cell(self, x, y, w, h, label, color):
        """Filled matrix cell with white label."""
        self.parts.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{color}"/>')
        self.text(x + w / 2, y + h / 2 + 4, label, 11, 600, "#fff", "middle")

    # ---------------- composite helpers
    def card_row(self, x, y, w, h, cards, gap=16, **kw):
        """cards = list of dicts(title, body, icon, accent, badge, pill). Returns list of (x,y,w,h)."""
        boxes = []
        for i, c in enumerate(cards):
            cx = x + i * (w + gap)
            self.card(cx, y, w, h, **{**kw, **c})
            boxes.append((cx, y, w, h))
        return boxes

    def card_col(self, x, y, w, h, cards, gap=16, **kw):
        boxes = []
        for i, c in enumerate(cards):
            cy = y + i * (h + gap)
            self.card(x, cy, w, h, **{**kw, **c})
            boxes.append((x, cy, w, h))
        return boxes

    def sequence(self, x, y, w, actors, messages, lane_h=36, actor_h=48):
        """Sequence diagram. actors = [(name, icon, color)]; messages = [(from_idx, to_idx, label, color, dashed)].
        Self-messages (from == to) draw a loop on the right, or on the left for the last actor. Returns bottom y."""
        n = len(actors)
        step = w / n
        bw = min(step - 14, 230)
        xs = [x + step * (i + 0.5) for i in range(n)]
        for i, (name, ic, col) in enumerate(actors):
            cx = xs[i]
            self.parts.append(f'<rect x="{cx - bw / 2:.0f}" y="{y}" width="{bw:.0f}" height="{actor_h}" rx="5" fill="#fff" stroke="{C.border}" stroke-width="1"/>')
            self.parts.append(f'<rect x="{cx - bw / 2:.0f}" y="{y}" width="4" height="{actor_h}" fill="{col}"/>')
            tx = cx - bw / 2 + 14
            if ic:
                self.icon(cx - bw / 2 + 12, y + 12, ic, 0.5)
                tx = cx - bw / 2 + 46
            ls = wrap(name, 13, bw - (tx - (cx - bw / 2)) - 8, 600)
            if len(ls) == 1:
                self.text(tx, y + 30, ls[0], 13, 600, C.ink)
            else:
                self.text(tx, y + 22, ls[0], 13, 600, C.ink)
                self.text(tx, y + 38, ls[1], 13, 600, C.ink)
                if len(ls) > 2:
                    self.warnings.append(f"OVERFLOW actor name: {name!r}")
        top = y + actor_h
        bottom = top + lane_h * (len(messages) + 1)
        for cx in xs:
            self.line(cx, top, cx, bottom, C.border, 1, dashed=True)
        yy = top + lane_h
        for (a, b, label, col, dashed) in messages:
            xa, xb = xs[a], xs[b]
            if a == b:
                right = a < n - 1
                sgn = 1 if right else -1
                self.arrow([(xa, yy - 8), (xa + sgn * 46, yy - 8), (xa + sgn * 46, yy + 8), (xa + sgn * 4, yy + 8)], col, dashed=dashed, sw=1.6)
                avail = step - 52
                ls = wrap(label, 11.5, avail)
                if len(ls) > 2:
                    self.warnings.append(f"OVERFLOW self-message label: {label!r}")
                for li, line in enumerate(ls[:2]):
                    if right:
                        self.text(xa + 56, yy - 2 + li * 15, line, 11.5, 400, C.ink)
                    else:
                        self.text(xa - 56, yy - 2 + li * 15, line, 11.5, 400, C.ink, "end")
            else:
                self.arrow([(xa + (4 if xa < xb else -4), yy), (xb - (6 if xa < xb else -6), yy)], col, dashed=dashed, sw=1.6)
                mx = (xa + xb) / 2
                tw = text_width(label, 11.5) + 10
                if tw > abs(xb - xa) * 1.7:
                    self.warnings.append(f"OVERFLOW message label much longer than its arrow: {label!r}")
                self.parts.append(f'<rect x="{mx - tw / 2:.0f}" y="{yy - 18}" width="{tw:.0f}" height="16" rx="3" fill="#fff" opacity="0.95"/>')
                self.text(mx, yy - 6, label, 11.5, 400, C.ink, "middle")
            yy += lane_h
        self._touch(bottom)
        return bottom

    def timeline(self, x, y, w, ticks, events, color=C.blue, tick_size=11):
        """Horizontal timeline. ticks = [(pos 0..1, label)]; events = [(pos, title, body, color)] placed alternating above/below."""
        self.parts.append(f'<rect x="{x}" y="{y - 3}" width="{w}" height="6" rx="3" fill="{color}" opacity="0.35"/>')
        for pos, label in ticks:
            px = x + pos * w
            self.line(px, y - 8, px, y + 8, color, 2)
            self.text(px, y + 24, label, tick_size, 600, C.ink, "middle")
        for i, (pos, title, body, col) in enumerate(events):
            px = x + pos * w
            self.parts.append(f'<circle cx="{px}" cy="{y}" r="7" fill="{col}" stroke="#fff" stroke-width="2"/>')
            above = i % 2 == 0
            body = [body] if isinstance(body, str) else list(body)
            nlines = sum(len(wrap(b, 11, 190 - 26)) for b in body)
            bh = 30 + 16 * nlines
            by = y - 48 - bh if above else y + 44
            bw = 190
            bx = min(max(px - bw / 2, x), x + w - bw)
            self.line(px, y - 10 if above else y + 10, px, by + bh if above else by, col, 1.2)
            self.card(bx, by, bw, bh, title, body, accent=col, shadow=False, title_size=12.5, body_size=11)

    def note_bottom(self, s, size=11):
        """Footnote line just above the footer rule (numbers, control references)."""
        self.text(32, self.h - 46, s, size, 400, C.grey, max_w=1216)

    def footer(self):
        y = self.h - 34
        self.parts.append(f'<line x1="32" y1="{y}" x2="1248" y2="{y}" stroke="{C.rule}"/>')
        self.parts.append(f'<text x="32" y="{y + 20}" font-family="{FONT}" font-size="11" fill="{C.light}">Generalised design: no client names, tenant IDs, addresses or data. Icons are simplified originals, not Microsoft artwork.</text>')
        self.parts.append(f'<text x="1248" y="{y + 20}" font-family="{FONT}" font-size="11" fill="{C.light}" text-anchor="end">Rich Dieu · github.com/richdieu-max</text>')

    def render(self, path):
        if self.min_bottom > self.h - 40:
            self.warnings.append(f"OVERFLOW canvas: content reaches {self.min_bottom:.0f}px but the footer rule is at {self.h - 34}px (height={self.h})")
        head = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 {self.h}" width="1280" height="{self.h}" role="img" aria-label="{esc(self.aria)}">\n'
                f'<title>{esc(self.title)}</title>\n'
                f'<defs>{"".join(self.markers.values())}</defs>\n'
                f'<rect width="1280" height="{self.h}" fill="#fff"/>\n'
                f'<rect x="0" y="0" width="1280" height="6" fill="{self.accent}"/>\n'
                f'<text x="32" y="48" font-family="{FONT}" font-size="22" font-weight="600" fill="{C.ink}">{esc(self.title)}</text>\n'
                f'<text x="32" y="72" font-family="{FONT}" font-size="13.5" fill="{C.grey}">{esc(self.subtitle)}</text>\n')
        self.footer()
        body = "\n".join(self.parts)
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(head + body + "\n</svg>\n")
        for w in self.warnings:
            print(f"  WARN {os.path.basename(path)}: {w}")
        return self.warnings
