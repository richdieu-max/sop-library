"""Vendor looks for figures about AWS and Red Hat.

A figure created with `Diagram(..., vendor="AWS")` or `vendor="Red Hat"` is drawn with the same kit and the
same dark-theme pass as every other figure, then restyled here:

- AWS: deep navy canvas with "squid ink" cards, orange as the lead accent, square corners, and icons as
  white glyphs on a tile coloured by service category (compute orange, storage green, security red,
  networking purple, management pink, database magenta). Specs draw Region groups with a dashed teal
  border, VPCs in purple and the account in pink.
- Red Hat: near-black canvas, Red Hat red as the lead accent, the Red Hat type family first in the font
  stack, tight corners, and flat white icons with red details.

Only the look follows each vendor's conventions. The icons are this library's own simplified glyphs, not
either vendor's icon set or logo.
"""

import re

_WHITE = {"#fff", "#ffffff", "white"}
_ATTR = re.compile(r'(fill|stroke)="([^"]+)"')

AWS_CATEGORY = {
    "compute": "#ED7100", "storage": "#7AA116", "security": "#DD344C",
    "network": "#8C4FFF", "management": "#E7157B", "database": "#C925D1", "general": "#5A6B86",
}
_AWS_ICONS = {
    "compute": "server server-stack vm-cluster chip laptop laptop-grey terminal terminal-blue app-window gear gear-box devices monitor",
    "storage": "ssd folder folder-share refresh-green package download",
    "security": "lock key shield-check shield-x defender-shield policy-shield entra-user user users id-card certificate breakglass firewall",
    "network": "globe ports-blue ports-green arrows-lr arrows-lr-circle link ip-server hierarchy sync-purple wifi cloud",
    "management": "chart-monitor doc-search doc-search-grey bell calendar list-blue target target-teal wrench clock checklist-purple "
                  "dollar document code-braces hash-doc bar-chart app-monitor",
    "database": "sql db-globe db-blue",
}
_AWS_TILE = {name: AWS_CATEGORY[cat] for cat, names in _AWS_ICONS.items() for name in names.split()}

FONTS = {
    "AWS": ("'Amazon Ember', 'Helvetica Neue', Helvetica, Arial, sans-serif", "'Amazon Ember Mono', Consolas, Menlo, monospace"),
    "Red Hat": ("'Red Hat Text', 'Red Hat Display', Overpass, 'Helvetica Neue', Arial, sans-serif", "'Red Hat Mono', Consolas, Menlo, monospace"),
}
RADIUS = {"AWS": "2", "Red Hat": "3"}

# Dark-theme colour (as written by theme.to_dark) -> vendor colour.
PALETTE = {
    "AWS": {
        "#0D1117": "#0F1B2A", "#151B23": "#16212F", "#1C2128": "#232F3E", "#181E26": "#1B2738",
        "#E6EDF3": "#FFFFFF", "#9198A1": "#B6BEC9", "#7D8590": "#8D99A8", "#3D444D": "#414D5C", "#30363D": "#354150",
        "#4493F8": "#539FE5", "#1F6FEB": "#0972D3", "#79C0FF": "#89BDEE", "#1158C7": "#033160",
        "#3FB950": "#9BC53D", "#238636": "#7AA116",
        "#F85149": "#FF7A85", "#DA3633": "#DD344C",
        "#D29922": "#FF9900", "#9E6A03": "#EC7211", "#E3B341": "#FFB84D",
        "#A371F7": "#B088FF", "#8957E5": "#8C4FFF",
        "#39C5CF": "#1FC8C9", "#1B7C83": "#00A4A6",
        "#121D2F": "#12293F", "#1A2E4A": "#163A5C",
        "#25171C": "#33161E", "#3A1D22": "#4A1A26",
        "#211D12": "#2E2110", "#272115": "#33240F", "#33290F": "#40290A",
        "#13201A": "#1C2A12", "#15221A": "#1F2E12", "#1B3222": "#293D14",
        "#1E182C": "#221A3D", "#221A32": "#261D45", "#2A1F3D": "#30245A",
        "#12231F": "#0C2B2E", "#13302E": "#0D3638",
    },
    "Red Hat": {
        "#0D1117": "#151515", "#151B23": "#1F1F1F", "#1C2128": "#292929", "#181E26": "#242424",
        "#E6EDF3": "#FFFFFF", "#9198A1": "#C7C7C7", "#7D8590": "#A3A3A3", "#3D444D": "#4D4D4D", "#30363D": "#383838",
        "#4493F8": "#92C5F9", "#1F6FEB": "#0066CC", "#79C0FF": "#B9DAFC", "#1158C7": "#004D99",
        "#3FB950": "#87BB62", "#238636": "#3D7317",
        "#F85149": "#F56E6E", "#DA3633": "#EE0000",
        "#D29922": "#F5C12E", "#9E6A03": "#B98412", "#E3B341": "#FFE072",
        "#A371F7": "#B6A6E9", "#8957E5": "#5E40BE",
        "#39C5CF": "#63BDBD", "#1B7C83": "#37A3A3",
        "#121D2F": "#0F2338", "#1A2E4A": "#003366",
        "#25171C": "#2B1414", "#3A1D22": "#3F0000",
        "#211D12": "#2B2310", "#272115": "#302710", "#33290F": "#3D2F0A",
        "#13201A": "#18240F", "#15221A": "#1B2911", "#1B3222": "#20360F",
        "#1E182C": "#1E1838", "#221A32": "#21134D", "#2A1F3D": "#2A1F5C",
        "#12231F": "#0F2A2A", "#13302E": "#004D4D",
    },
}


def icon_markup(vendor, name, inner):
    """The inside of an icon's 48 x 48 group, restyled for the vendor."""
    if vendor == "AWS":
        tile = _AWS_TILE.get(name, AWS_CATEGORY["general"])
        glyph = _ATTR.sub(lambda m: m.group(0) if m.group(2) == "none" else
                          f'{m.group(1)}="{tile if m.group(2).lower() in _WHITE else "#FFFFFF"}"', inner)
        return f'<rect x="0" y="0" width="48" height="48" rx="5" fill="{tile}"/><g transform="translate(7,7) scale(0.7083)">{glyph}</g>'
    if vendor == "Red Hat":
        return _ATTR.sub(lambda m: m.group(0) if m.group(2) == "none" else
                         f'{m.group(1)}="{"#EE0000" if m.group(2).lower() in _WHITE else "#FFFFFF"}"', inner)
    return inner


def restyle(svg, vendor, font, mono):
    """Apply the vendor palette, type and corner radius to a figure already mapped to the dark theme."""
    if vendor not in PALETTE:
        return svg
    pal = PALETTE[vendor]
    svg = re.sub(r"#[0-9A-Fa-f]{6}\b", lambda m: pal.get(m.group(0).upper(), m.group(0)), svg)
    new_font, new_mono = FONTS[vendor]
    svg = svg.replace(f'font-family="{font}"', f'font-family="{new_font}"').replace(f'font-family="{mono}"', f'font-family="{new_mono}"')
    return re.sub(r'rx="[56]"', f'rx="{RADIUS[vendor]}"', svg)
