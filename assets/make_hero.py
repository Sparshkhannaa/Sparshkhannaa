"""Draws the profile banner: a name written on a contribution-style grid (53 weeks x 7 days), with a slow heat
wave running through the letters and a few cells flickering at the edges.
Run: python assets/make_hero.py   ->  assets/hero-dark.svg, assets/hero-light.svg"""
import random
from pathlib import Path

NAME = "SPARSH"
COLS, ROWS, CELL, GAP = 53, 7, 12, 3
WAVE_S, STEP_S = 5.0, 0.14  # one colour cycle, and the lag between neighbouring columns

FONT = {  # 5 x 7 pixel letters
    "S": [".###.", "#...#", "#....", ".###.", "....#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
}

THEMES = {  # empty cell, three letter colours (trough to crest), still edge cell, two flicker colours
    "dark": {"empty": "#1c1a26", "letter": ["#d9482f", "#f58a1f", "#fcd34d"], "still": "#3a1548", "flick": ["#5a1a5e", "#a52c60"]},
    "light": {"empty": "#edebf1", "letter": ["#6a176e", "#b3275f", "#e2552b"], "still": "#f3dcc4", "flick": ["#f6d2a8", "#f0a35e"]},
}


def cell(c, r, extra=""):
    return f'<rect x="{c * (CELL + GAP)}" y="{r * (CELL + GAP)}" width="{CELL}" height="{CELL}" rx="2.5"{extra}/>'


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
    flick, still = edge[:22], set(edge[22:32])

    out = [f'<g fill="{t["empty"]}">']
    out += [cell(c, r) for c in range(COLS) for r in range(ROWS) if r not in lit.get(c, []) and (c, r) not in still and (c, r) not in flick]
    out.append("</g>")
    out.append(f'<g fill="{t["still"]}">' + "".join(cell(c, r) for c, r in sorted(still)) + "</g>")
    for c, r in sorted(flick):
        out.append(cell(c, r, f' class="f" style="animation-duration:{rng.uniform(7, 13):.1f}s;animation-delay:-{rng.uniform(0, 13):.1f}s"'))
    for c in sorted(lit):
        delay = WAVE_S - ((c - start) * STEP_S) % WAVE_S
        out.append(f'<g class="l" style="animation-delay:-{delay:.2f}s">' + "".join(cell(c, r) for r in lit[c]) + "</g>")

    w, h = COLS * (CELL + GAP) - GAP, ROWS * (CELL + GAP) - GAP
    a, b, m = t["letter"]
    style = f"""
.l {{ fill: {b}; animation: wave {WAVE_S}s ease-in-out infinite; }}
.f {{ fill: {t["empty"]}; animation: flick 9s linear infinite; }}
@keyframes wave {{ 0%, 100% {{ fill: {a}; }} 35%, 65% {{ fill: {b}; }} 50% {{ fill: {m}; }} }}
@keyframes flick {{ 0%, 68%, 100% {{ fill: {t["empty"]}; }} 76%, 92% {{ fill: {t["flick"][0]}; }} 84% {{ fill: {t["flick"][1]}; }} }}
@media (prefers-reduced-motion: reduce) {{ .l, .f {{ animation: none; }} }}
"""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 {w + 8} {h + 8}" role="img" aria-label="{NAME.title()}">\n'
            f"<title>{NAME.title()}</title>\n<style>{style}</style>\n" + "\n".join(out) + "\n</svg>\n")


if __name__ == "__main__":
    here = Path(__file__).parent
    for theme in THEMES:
        (here / f"hero-{theme}.svg").write_text(build(theme), encoding="utf-8", newline="\n")
        print("wrote", here / f"hero-{theme}.svg")
