"""Draws the profile banner: a name built as a 3D skyline on a contribution-style grid (53 weeks x 7 days).
A heat wave runs through the letters, raising each column and turning it hotter as it passes, and small
hotspots pop up at the edges.
Run: python assets/make_hero.py   ->  assets/hero-dark.svg, assets/hero-light.svg"""
import random
from pathlib import Path

NAME = "SPARSH"
COLS, ROWS = 53, 7
PITCH, SIZE = 15, 0.8  # cell spacing in px, and the share of it a cell fills
KX, KY = 6, 13  # how far one row back moves a cell right and up
LOW, HIGH = 4, 22  # letter height in px at the trough and the crest of the wave; much taller hides the letter shapes
WAVE_S, STEP_S = 5.0, 0.14  # one wave cycle, and the lag between neighbouring columns
PAD = 8

FONT = {  # 5 x 7 pixel letters
    "S": [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
}

THEMES = {  # ground tile, letter colour at trough and crest, still tower, hotspot colours, shade of front and side faces
    "dark": {"empty": "#1c1a26", "letter": ["#d9482f", "#fcd34d"], "still": "#4a1a5c", "pop": ["#6b1f6e", "#c2356a"],
             "shade": [0.52, 0.34], "glow": ("#f58a1f", 0.20)},
    "light": {"empty": "#e9e6ef", "letter": ["#6a176e", "#e2552b"], "still": "#eebf94", "pop": ["#f3c592", "#ee9a4d"],
              "shade": [0.72, 0.50], "glow": ("#6a176e", 0.10)},
}


def shade(colour, k):
    return "#" + "".join(f"{round(int(colour[i:i + 2], 16) * k):02x}" for i in (1, 3, 5))


def at(cx, ry, h=0):
    """Screen position of a grid point: columns run right, rows run toward the viewer, h is height."""
    return round(cx * PITCH + (ROWS - ry) * KX, 1), round(ry * KY - h, 1)


def pts(*p):
    return " ".join(f"{x},{y}" for x, y in p)


def top(c, r, h=0, extra=""):
    return f'<polygon{extra} points="{pts(at(c, r, h), at(c + SIZE, r, h), at(c + SIZE, r + SIZE, h), at(c, r + SIZE, h))}"/>'


def still_tower(c, r, h, colour, k):
    f, s = r + SIZE, c + SIZE
    return (f'<polygon fill="{shade(colour, k[1])}" points="{pts(at(s, f, h), at(s, r, h), at(s, r), at(s, f))}"/>'
            f'<polygon fill="{shade(colour, k[0])}" points="{pts(at(c, f, h), at(s, f, h), at(s, f), at(c, f))}"/>'
            + top(c, r, h, f' fill="{colour}"'))


def moving_tower(c, r):
    """Faces are 1px tall and stretched by the stylesheet, so one set of keyframes drives every tower."""
    (fx, fy), (sx, sy) = at(c, r + SIZE), at(c + SIZE, r + SIZE)
    return (f'<g transform="matrix({KX * SIZE} {-KY * SIZE} 0 1 {sx} {sy})"><rect class="sd" y="-1" width="1" height="1"/></g>'
            f'<g transform="translate({fx} {fy})"><rect class="fr" y="-1" width="{PITCH * SIZE}" height="1"/></g>'
            + top(c, r, 0, ' class="tp"'))


def build(theme):
    t = THEMES[theme]
    start = (COLS - (len(NAME) * 6 - 1)) // 2
    lit = {}  # column -> rows that belong to a letter
    for i, ch in enumerate(NAME):
        for r, line in enumerate(FONT[ch]):
            for c, px in enumerate(line):
                if px == "#":
                    lit.setdefault(start + i * 6 + c, []).append(r)

    rng = random.Random(7)
    edge = [(c, r) for c in range(COLS) for r in range(ROWS) if c < start - 1 or c > start + len(NAME) * 6 - 1]
    rng.shuffle(edge)
    pop = {p: (rng.uniform(7, 13), rng.uniform(0, 13)) for p in edge[:22]}
    still = set(edge[22:32])

    w, h = (COLS - 1 + SIZE) * PITCH + ROWS * KX, HIGH + (ROWS - 1 + SIZE) * KY
    gx, gy = at(COLS / 2, ROWS / 2 + 1)
    out = [f'<g transform="translate({PAD} {HIGH + PAD})">', f'<g fill="{t["empty"]}">']
    out += [top(c, r) for c in range(COLS) for r in range(ROWS) if r not in lit.get(c, [])]
    out.append("</g>")
    out.append(f'<ellipse cx="{gx}" cy="{gy}" rx="{len(NAME) * 3.6 * PITCH}" ry="{ROWS * KY * 0.9}" fill="url(#glow)"/>')
    for c in range(COLS):  # left to right, back to front, so nearer towers are drawn over farther ones
        if c in lit:
            delay = WAVE_S - ((c - start) * STEP_S) % WAVE_S
            out.append(f'<g class="l" style="--d:-{delay:.2f}s">' + "".join(moving_tower(c, r) for r in lit[c]) + "</g>")
        for r in range(ROWS):
            if (c, r) in still:
                out.append(still_tower(c, r, 4, t["still"], t["shade"]))
            elif (c, r) in pop:
                out.append(f'<g class="p" style="--t:{pop[c, r][0]:.1f}s;--d:-{pop[c, r][1]:.1f}s">{moving_tower(c, r)}</g>')
    out.append("</g>")

    (a, m), (p0, p1), (kf, ks) = t["letter"], t["pop"], t["shade"]
    mid = (LOW + HIGH) // 2
    faces = [("tp", 1, "translateY(-{}px)"), ("fr", kf, "scaleY({})"), ("sd", ks, "scaleY({})")]
    css = [".fr, .sd { transform-box: fill-box; transform-origin: 50% 100%; }"]
    for cls, k, tf in faces:
        base = t["empty"] if cls == "tp" else shade(p0, k)
        css.append(f".l .{cls} {{ fill: {shade(a, k)}; transform: {tf.format(mid)}; animation: l{cls} {WAVE_S}s ease-in-out var(--d) infinite; }}")
        css.append(f".p .{cls} {{ fill: {base}; transform: {tf.format(0)}; animation: p{cls} var(--t) linear var(--d) infinite; }}")
        css.append(f"@keyframes l{cls} {{ 0%, 100% {{ fill: {shade(a, k)}; transform: {tf.format(LOW)}; }} 50% {{ fill: {shade(m, k)}; transform: {tf.format(HIGH)}; }} }}")
        css.append(f"@keyframes p{cls} {{ 0%, 68%, 100% {{ fill: {base}; transform: {tf.format(0)}; }} "
                   f"76%, 92% {{ fill: {shade(p0, k)}; transform: {tf.format(6)}; }} 84% {{ fill: {shade(p1, k)}; transform: {tf.format(14)}; }} }}")
    css.append("@media (prefers-reduced-motion: reduce) { .l *, .p * { animation: none; } }")

    glow, opacity = t["glow"]
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w + 2 * PAD:.0f} {h + 2 * PAD:.0f}" role="img" aria-label="{NAME.title()}">\n'
            f"<title>{NAME.title()}</title>\n<style>\n" + "\n".join(css) + "\n</style>\n"
            f'<defs><radialGradient id="glow"><stop offset="0" stop-color="{glow}" stop-opacity="{opacity}"/>'
            f'<stop offset="1" stop-color="{glow}" stop-opacity="0"/></radialGradient></defs>\n' + "\n".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    here = Path(__file__).parent
    for theme in THEMES:
        (here / f"hero-{theme}.svg").write_text(build(theme), encoding="utf-8", newline="\n")
        print("wrote", here / f"hero-{theme}.svg")
