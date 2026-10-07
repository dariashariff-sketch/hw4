"""Draws the cartoon bulldog category tiles as SVGs into public/categories/.

One shared bulldog (head, legs, paws) + a different garment per category.
Run from frontend/:  python scripts/draw_bulldogs.py
Photos named <slug>.png/.jpg in the same folder take priority over these SVGs.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "public" / "categories"

NAVY, NAVY_DARK, NAVY_LIGHT = "#00356b", "#00254a", "#2a5a8f"
FUR, FUR_DARK, FUR_LIGHT = "#d9a066", "#b9824a", "#f6e6cf"
INK, BG, GOLD = "#2b1d14", "#e3ebf5", "#ffffff"


def head(tongue: bool = False) -> str:
    t = (
        f'<path d="M93 124 Q100 136 107 124 Z" fill="#e8737a" stroke="{INK}" stroke-width="1.5"/>'
        if tongue
        else ""
    )
    return f"""
  <!-- floppy rose ears -->
  <path d="M62 56 Q40 46 26 60 Q30 66 40 66 Q46 80 54 74 Z" fill="{FUR_DARK}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M138 56 Q160 46 174 60 Q170 66 160 66 Q154 80 146 74 Z" fill="{FUR_DARK}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  <!-- wide, flat head with droopy jowls -->
  <path d="M100 46 C140 46 162 60 164 84 C166 102 158 114 146 120 C140 130 126 134 112 130 Q100 134 88 130
           C74 134 60 130 54 120 C42 114 34 102 36 84 C38 60 60 46 100 46 Z"
        fill="{FUR}" stroke="{INK}" stroke-width="2.5"/>
  <!-- white blaze + muzzle -->
  <path d="M93 48 Q100 46 107 48 L110 88 Q100 92 90 88 Z" fill="{FUR_LIGHT}"/>
  <path d="M64 106 C64 92 82 88 100 90 C118 88 136 92 136 106 C136 122 122 130 112 128 Q100 132 88 128 C78 130 64 122 64 106 Z" fill="{FUR_LIGHT}"/>
  <!-- forehead wrinkles -->
  <path d="M78 62 Q88 57 96 62 M104 62 Q112 57 122 62" stroke="{FUR_DARK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <path d="M84 54 Q91 51 96 54 M104 54 Q109 51 116 54" stroke="{FUR_DARK}" stroke-width="2" fill="none" stroke-linecap="round"/>
  <!-- wide-set eyes -->
  <circle cx="72" cy="82" r="7.5" fill="{INK}"/><circle cx="128" cy="82" r="7.5" fill="{INK}"/>
  <circle cx="74.5" cy="79.5" r="2.6" fill="#fff"/><circle cx="130.5" cy="79.5" r="2.6" fill="#fff"/>
  <!-- blush -->
  <ellipse cx="56" cy="102" rx="7" ry="4" fill="#f2a0a0" opacity=".55"/>
  <ellipse cx="144" cy="102" rx="7" ry="4" fill="#f2a0a0" opacity=".55"/>
  <!-- the classic bulldog nose roll -->
  <path d="M80 92 Q100 80 120 92" stroke="{FUR_DARK}" stroke-width="3" fill="none" stroke-linecap="round"/>
  <!-- short pushed-up nose -->
  <path d="M86 96 Q100 90 114 96 Q114 105 100 107 Q86 105 86 96 Z" fill="{INK}"/>
  <ellipse cx="94" cy="96" rx="3.5" ry="1.6" fill="#fff" opacity=".5"/>
  <path d="M100 107 L100 111" stroke="{INK}" stroke-width="2.5" stroke-linecap="round"/>
  <!-- droopy flews -->
  <path d="M76 113 Q88 115 100 111 Q112 115 124 113" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  <!-- happy underbite smile -->
  <path d="M78 114 Q100 138 122 114 Q100 122 78 114 Z" fill="#7a3b3b"/>
  <path d="M78 114 Q100 138 122 114" stroke="{INK}" stroke-width="2.5" fill="none" stroke-linecap="round"/>
  {t}
  <rect x="86" y="118" width="5" height="6" rx="1.5" fill="#fff" stroke="{INK}" stroke-width="1.2"/>
  <rect x="109" y="118" width="5" height="6" rx="1.5" fill="#fff" stroke="{INK}" stroke-width="1.2"/>
"""


def paws() -> str:
    return f"""
  <ellipse cx="74" cy="188" rx="15" ry="9" fill="{FUR}" stroke="{INK}" stroke-width="2.5"/>
  <ellipse cx="126" cy="188" rx="15" ry="9" fill="{FUR}" stroke="{INK}" stroke-width="2.5"/>
  <path d="M69 184 L69 191 M74 183 L74 192 M79 184 L79 191 M121 184 L121 191 M126 183 L126 192 M131 184 L131 191"
        stroke="{FUR_DARK}" stroke-width="1.6" stroke-linecap="round"/>
"""


TORSO = "M40 200 C40 156 60 126 100 124 C140 126 160 156 160 200 Z"


def legs(fill: str, top: int = 148) -> str:
    """Front legs (or sleeves when fill is a garment color). Wide bulldog stance."""
    return f"""
  <path d="M58 {top} Q54 170 60 186 L89 186 Q93 168 88 {top + 2} Z" fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M142 {top} Q146 170 140 186 L111 186 Q107 168 112 {top + 2} Z" fill="{fill}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
"""


def cuffs(color: str) -> str:
    return f"""
  <rect x="59" y="176" width="30" height="10" rx="3" fill="{color}" stroke="{INK}" stroke-width="2"/>
  <rect x="111" y="176" width="30" height="10" rx="3" fill="{color}" stroke="{INK}" stroke-width="2"/>
"""


def svg(body: str, title: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" role="img" aria-label="{title}">
  <title>{title}</title>
  <rect width="200" height="200" rx="24" fill="{BG}"/>
  <circle cx="100" cy="104" r="84" fill="#fff" opacity=".55"/>
  <circle cx="34" cy="34" r="4" fill="{GOLD}"/><circle cx="168" cy="44" r="3" fill="{GOLD}"/><circle cx="160" cy="26" r="2" fill="{NAVY_LIGHT}"/>
{body}
</svg>
"""


def hoodie() -> str:
    return svg(
        f"""
  <!-- hood up behind the head -->
  <path d="M100 26 C152 26 180 58 178 98 C176 124 160 138 148 142 L52 142 C40 138 24 124 22 98 C20 58 48 26 100 26 Z"
        fill="{NAVY}" stroke="{INK}" stroke-width="2.5"/>
  <path d="M100 34 C146 34 170 62 168 96 C166 118 154 130 144 134 L56 134 C46 130 34 118 32 96 C30 62 54 34 100 34 Z" fill="{NAVY_DARK}"/>
  <path d="{TORSO}" fill="{NAVY}" stroke="{INK}" stroke-width="2.5"/>
  {head()}
  <!-- drawstrings -->
  <path d="M84 132 L80 160 M116 132 L120 160" stroke="#fff" stroke-width="3" stroke-linecap="round"/>
  <circle cx="80" cy="162" r="3" fill="#fff"/><circle cx="120" cy="162" r="3" fill="#fff"/>
  <!-- kangaroo pocket (peeks out between the legs) -->
  <path d="M66 164 L134 164 L140 192 L60 192 Z" fill="{NAVY_LIGHT}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>
  {legs(NAVY)}
  {cuffs(NAVY_DARK)}
  {paws()}
""",
        "Bulldog in a navy hoodie",
    )


def crewneck() -> str:
    gray, gray_dark = "#a7adb5", "#7e858f"
    return svg(
        f"""
  <path d="{TORSO}" fill="{gray}" stroke="{INK}" stroke-width="2.5"/>
  <!-- heather speckles -->
  <g fill="{gray_dark}" opacity=".6"><circle cx="56" cy="170" r="1.5"/><circle cx="146" cy="164" r="1.5"/><circle cx="100" cy="158" r="1.5"/>
  <circle cx="104" cy="178" r="1.5"/><circle cx="96" cy="190" r="1.5"/><circle cx="150" cy="190" r="1.5"/><circle cx="48" cy="192" r="1.5"/></g>
  <!-- navy chest stripe -->
  <path d="M50 158 Q100 150 150 158" stroke="{NAVY}" stroke-width="5" fill="none" stroke-linecap="round"/>
  {head()}
  <!-- ribbed crew collar hugging the jowls -->
  <path d="M60 124 Q100 144 140 124 L143 133 Q100 154 57 133 Z" fill="{gray_dark}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M68 130 L67 136 M79 135 L78 141 M90 138 L90 144 M100 139 L100 145 M110 138 L110 144 M121 135 L122 141 M132 130 L133 136" stroke="{INK}" stroke-width="1" opacity=".5"/>
  {legs(gray)}
  {cuffs(gray_dark)}
  {paws()}
""",
        "Bulldog in a gray crewneck sweatshirt",
    )


def tshirt() -> str:
    return svg(
        f"""
  <path d="{TORSO}" fill="#ffffff" stroke="{INK}" stroke-width="2.5"/>
  {head(tongue=True)}
  <!-- navy collar trim -->
  <path d="M64 126 Q100 146 136 126" stroke="{NAVY}" stroke-width="5" fill="none" stroke-linecap="round"/>
  {legs(FUR, top=150)}
  <!-- short sleeves over the shoulders -->
  <path d="M52 134 Q40 150 48 166 L82 160 Q84 144 74 132 Z" fill="#fff" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M148 134 Q160 150 152 166 L118 160 Q116 144 126 132 Z" fill="#fff" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>
  <path d="M50 163 L81 157 M150 163 L119 157" stroke="{NAVY}" stroke-width="4" stroke-linecap="round"/>
  {paws()}
""",
        "Bulldog in a white T-shirt",
    )


def quarter_zip() -> str:
    return svg(
        f"""
  <path d="{TORSO}" fill="{NAVY}" stroke="{INK}" stroke-width="2.5"/>
  <!-- popped stand-up collar, tucked behind the jowls -->
  <path d="M48 110 L58 136 L100 144 L142 136 L152 110 L130 126 L100 132 L70 126 Z" fill="{NAVY_LIGHT}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>
  {head()}
  <!-- the quarter zip -->
  <path d="M100 132 L100 166" stroke="#c9d3df" stroke-width="5" stroke-linecap="round"/>
  <path d="M100 132 L100 166" stroke="{INK}" stroke-width="1.2" stroke-dasharray="2 2"/>
  <rect x="95.5" y="140" width="9" height="14" rx="3" fill="#e9eef4" stroke="{INK}" stroke-width="1.8"/>
  <circle cx="100" cy="149" r="1.6" fill="{INK}"/>
  <!-- white piping -->
  <path d="M62 144 Q80 150 96 148 M104 148 Q120 150 138 144" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/>
  {legs(NAVY)}
  {cuffs(NAVY_DARK)}
  {paws()}
""",
        "Bulldog in a navy quarter-zip",
    )


def fleece() -> str:
    cream, cream_dark = "#f3ead8", "#d9cdb4"
    bumps = "".join(
        f'<circle cx="{x}" cy="{y}" r="3.2" fill="{cream_dark}" opacity=".75"/>'
        for x, y in [(52, 166), (62, 150), (48, 186), (92, 176), (148, 166), (138, 150), (152, 186),
                     (108, 186), (82, 146), (118, 146), (94, 160), (106, 162)]
    )
    return svg(
        f"""
  <path d="{TORSO}" fill="{cream}" stroke="{INK}" stroke-width="2.5"/>
  {bumps}
  <!-- big fleece collar -->
  <path d="M44 108 Q46 140 97 142 L97 130 Q64 128 56 104 Z" fill="{cream}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>
  <path d="M156 108 Q154 140 103 142 L103 130 Q136 128 144 104 Z" fill="{cream}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>
  {head()}
  <!-- full zip with navy trim -->
  <path d="M100 132 L100 200" stroke="{NAVY}" stroke-width="7"/>
  <path d="M100 132 L100 200" stroke="#c9d3df" stroke-width="1.5" stroke-dasharray="2 2"/>
  <rect x="95.5" y="138" width="9" height="13" rx="3" fill="{NAVY_DARK}" stroke="{INK}" stroke-width="1.6"/>
  {legs(cream)}
  <g fill="{cream_dark}" opacity=".75"><circle cx="66" cy="160" r="3"/><circle cx="80" cy="170" r="3"/><circle cx="120" cy="160" r="3"/><circle cx="134" cy="170" r="3"/></g>
  {cuffs(NAVY)}
  {paws()}
""",
        "Bulldog in a cream sherpa fleece jacket",
    )


def long_sleeve() -> str:
    return svg(
        f"""
  <path d="{TORSO}" fill="{NAVY}" stroke="{INK}" stroke-width="2.5"/>
  <!-- athletic side panels -->
  <path d="M42 178 Q48 150 62 134 L68 142 Q56 160 52 198 Z" fill="{NAVY_LIGHT}"/>
  <path d="M158 178 Q152 150 138 134 L132 142 Q144 160 148 198 Z" fill="{NAVY_LIGHT}"/>
  {head()}
  <!-- v-neck -->
  <path d="M68 128 L100 148 L132 128" stroke="#fff" stroke-width="4" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  {legs(NAVY)}
  <!-- sporty sleeve stripes -->
  <path d="M57 162 L90 162 M57 168 L90 168 M110 162 L143 162 M110 168 L143 168" stroke="{GOLD}" stroke-width="3"/>
  {cuffs(NAVY_DARK)}
  {paws()}
""",
        "Bulldog in a navy long-sleeve performance shirt",
    )


DRAWINGS = {
    "hoodies": hoodie,
    "crewnecks": crewneck,
    "t-shirts": tshirt,
    "quarter-zips": quarter_zip,
    "jackets-fleece": fleece,
    "long-sleeves": long_sleeve,
}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for slug, draw in DRAWINGS.items():
        (OUT / f"{slug}.svg").write_text(draw(), encoding="utf-8")
        print("wrote", OUT / f"{slug}.svg")
