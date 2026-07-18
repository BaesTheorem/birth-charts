"""Assemble packet HTML from chart-data.json plus the work dir's content modules.

Usage: python pipeline/build.py work/<dir>

Expects in the work dir:
  chart-data.json, wheel-<slug>.svg (from compute.py)
  content_<slug>.py per subject, content_synastry.py for the pair (written by hand;
  see pipeline/content_guide.md). Each must define build(ctx) -> body HTML string.

Writes work/<dir>/out/<slug>.html and synastry.html.
"""
import html as htmllib
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CSS = (REPO / "pipeline" / "style.css").read_text()

SIGN_FULL = {"Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
             "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
             "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"}
SIGN_GLYPH = {"Ari": "♈", "Tau": "♉", "Gem": "♊", "Can": "♋", "Leo": "♌", "Vir": "♍",
              "Lib": "♎", "Sco": "♏", "Sag": "♐", "Cap": "♑", "Aqu": "♒", "Pis": "♓"}
SIGN_ELEMENT = {"Ari": "Fire", "Leo": "Fire", "Sag": "Fire",
                "Tau": "Earth", "Vir": "Earth", "Cap": "Earth",
                "Gem": "Air", "Lib": "Air", "Aqu": "Air",
                "Can": "Water", "Sco": "Water", "Pis": "Water"}
SIGN_MODE = {"Ari": "Cardinal", "Can": "Cardinal", "Lib": "Cardinal", "Cap": "Cardinal",
             "Tau": "Fixed", "Leo": "Fixed", "Sco": "Fixed", "Aqu": "Fixed",
             "Gem": "Mutable", "Vir": "Mutable", "Sag": "Mutable", "Pis": "Mutable"}
PLANET_GLYPH = {"Sun": "☉", "Moon": "☽", "Mercury": "☿", "Venus": "♀", "Mars": "♂",
                "Jupiter": "♃", "Saturn": "♄", "Uranus": "♅", "Neptune": "♆", "Pluto": "♇",
                "Chiron": "⚷", "Mean_Lilith": "⚸", "True_North_Lunar_Node": "☊",
                "True_South_Lunar_Node": "☋", "Ascendant": "ASC", "Medium_Coeli": "MC",
                "Descendant": "DSC", "Imum_Coeli": "IC"}
PLANET_LABEL = {"Mean_Lilith": "Black Moon Lilith", "True_North_Lunar_Node": "North Node",
                "True_South_Lunar_Node": "South Node", "Medium_Coeli": "Midheaven (MC)",
                "Ascendant": "Ascendant (Rising)", "Descendant": "Descendant",
                "Imum_Coeli": "Imum Coeli (IC)"}
ASPECT_GLYPH = {"conjunction": "☌", "opposition": "☍", "trine": "△", "square": "□",
                "sextile": "⚹", "quintile": "Q", "biquintile": "bQ", "quincunx": "⚻",
                "semi-sextile": "⚺", "semi-square": "∠", "sesquiquadrate": "⚼"}
HOUSE_ORD = ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th", "9th", "10th", "11th", "12th"]
HOUSE_KEY_ORD = ["first_house", "second_house", "third_house", "fourth_house", "fifth_house",
                 "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
                 "eleventh_house", "twelfth_house"]
HOUSE_NAME_TO_ORD = {"First_House": "1st", "Second_House": "2nd", "Third_House": "3rd",
                     "Fourth_House": "4th", "Fifth_House": "5th", "Sixth_House": "6th",
                     "Seventh_House": "7th", "Eighth_House": "8th", "Ninth_House": "9th",
                     "Tenth_House": "10th", "Eleventh_House": "11th", "Twelfth_House": "12th"}
MAIN_POINTS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
               "uranus", "neptune", "pluto", "chiron", "true_node", "mean_lilith"]
ANGLE_POINTS = ["ascendant", "medium_coeli", "descendant", "imum_coeli"]


def fmt_deg(pos):
    d = int(pos)
    m = round((pos - d) * 60)
    if m == 60:
        d, m = d + 1, 0
    return f"{d}°{m:02d}′"


def label(name):
    return PLANET_LABEL.get(name, name.replace("_", " "))


def positions_table(subj):
    rows = []
    for key in MAIN_POINTS + ANGLE_POINTS:
        p = subj["points"].get(key)
        if not p:
            continue
        retro = " ℞" if p.get("retrograde") else ""
        house = HOUSE_NAME_TO_ORD.get(p.get("house") or "", "—")
        rows.append(
            f"<tr><td class='gl'>{PLANET_GLYPH.get(p['name'], '')}</td><td>{label(p['name'])}</td>"
            f"<td class='gl'>{SIGN_GLYPH[p['sign']]}</td>"
            f"<td>{fmt_deg(p['position'])} {SIGN_FULL[p['sign']]}{retro}</td>"
            f"<td>{house}</td><td>{SIGN_ELEMENT[p['sign']]}</td><td>{SIGN_MODE[p['sign']]}</td></tr>")
    return ("<table class='data'><thead><tr><th></th><th>Point</th><th></th><th>Position</th>"
            "<th>House</th><th>Element</th><th>Mode</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def houses_table(subj):
    rows = []
    for i, key in enumerate(HOUSE_KEY_ORD):
        h = subj["houses"][key]
        rows.append(f"<tr><td>House {i+1}</td><td class='gl'>{SIGN_GLYPH[h['sign']]}</td>"
                    f"<td>{fmt_deg(h['position'])} {SIGN_FULL[h['sign']]}</td></tr>")
    return ("<table class='data'><thead><tr><th>Cusp</th><th></th><th>Sign</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def balance_tables(subj):
    """Element/modality tallies over the ten planets; angles noted in prose instead."""
    ten = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
    elems = {"Fire": [], "Earth": [], "Air": [], "Water": []}
    modes = {"Cardinal": [], "Fixed": [], "Mutable": []}
    for key in ten:
        p = subj["points"][key]
        elems[SIGN_ELEMENT[p["sign"]]].append(p["name"])
        modes[SIGN_MODE[p["sign"]]].append(p["name"])
    def tbl(d, title):
        rows = "".join(
            f"<tr><td>{k}</td><td class='num'>{len(v)}</td>"
            f"<td class='muted'>{', '.join(PLANET_GLYPH[n] for n in v) or '—'}</td></tr>"
            for k, v in d.items())
        return (f"<table class='data balance'><thead><tr><th>{title}</th><th>#</th><th>Planets</th>"
                f"</tr></thead><tbody>{rows}</tbody></table>")
    return tbl(elems, "Element"), tbl(modes, "Modality")


def aspects_table(aspects, dual=False, names=("", "")):
    rows = []
    for a in aspects:
        p1, p2 = label(a["p1_name"]), label(a["p2_name"])
        if dual:
            p1, p2 = f"{names[0]}’s {p1}", f"{names[1]}’s {p2}"
        rows.append(f"<tr><td>{PLANET_GLYPH.get(a['p1_name'], '')} {p1}</td>"
                    f"<td class='gl'>{ASPECT_GLYPH.get(a['aspect'], a['aspect'])}</td>"
                    f"<td>{a['aspect'].capitalize()}</td>"
                    f"<td>{PLANET_GLYPH.get(a['p2_name'], '')} {p2}</td>"
                    f"<td class='num'>{a['orbit']:.2f}°</td></tr>")
    return ("<table class='data aspects'><thead><tr><th>Point</th><th></th><th>Aspect</th>"
            "<th>Point</th><th>Orb</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


def overlay_house(abs_pos, houses):
    cusps = [houses[k]["abs_pos"] for k in HOUSE_KEY_ORD]
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        if a <= b:
            if a <= abs_pos < b:
                return i
        else:
            if abs_pos >= a or abs_pos < b:
                return i
    return None


def overlay_table(owner, partner, owner_name, partner_name):
    rows = []
    for key in ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
                "uranus", "neptune", "pluto"]:
        p = owner["points"][key]
        hi = overlay_house(p["abs_pos"], partner["houses"])
        rows.append(f"<tr><td class='gl'>{PLANET_GLYPH[p['name']]}</td><td>{p['name']}</td>"
                    f"<td>{fmt_deg(p['position'])} {SIGN_FULL[p['sign']]}</td>"
                    f"<td>{HOUSE_ORD[hi]} house</td></tr>")
    return (f"<table class='data'><thead><tr><th></th><th>{owner_name}’s planet</th>"
            f"<th>Position</th><th>Falls in {partner_name}’s…</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def score_table(score):
    """Discepolo scorecard: one row per scored item, then the total."""
    rows = []
    for item in score.get("breakdown", []):
        rows.append(f"<tr><td>{item['description']}</td>"
                    f"<td class='muted'>{item['details']}</td>"
                    f"<td class='num'>+{item['points']}</td></tr>")
    rows.append(f"<tr><td><b>Total</b></td><td class='muted'>{score['description']}</td>"
                f"<td class='num'><b>{score['value']}</b></td></tr>")
    return ("<table class='data'><thead><tr><th>Scored contact</th><th>Detail</th>"
            "<th>Points</th></tr></thead><tbody>" + "".join(rows) + "</tbody></table>")


GLYPH_CHARS = "♈♉♊♋♌♍♎♏♐♑♒♓☉☽☿♀♂♃♄♅♆♇⚷⚸☊☋"


def force_text_glyphs(html):
    """Append U+FE0E so Chromium renders glyphs as text, not color emoji."""
    VS = "︎"
    for ch in GLYPH_CHARS:
        html = html.replace(ch, ch + VS)
    return html.replace(VS + VS, VS)


def page(title, body):
    # Post-process glyphs outside inline SVGs only.
    parts, rest = [], body
    while "<svg" in rest:
        pre, rest = rest.split("<svg", 1)
        svg, rest = rest.split("</svg>", 1)
        parts.append(force_text_glyphs(pre))
        parts.append("<svg" + svg + "</svg>")
    parts.append(force_text_glyphs(rest))
    return (f"<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
            f"<title>{htmllib.escape(title)}</title>\n<style>{CSS}</style></head>"
            f"<body>{''.join(parts)}</body></html>")


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    workdir = Path(sys.argv[1]).resolve()
    data = json.loads((workdir / "chart-data.json").read_text())
    outdir = workdir / "out"
    outdir.mkdir(exist_ok=True)

    ctx = {
        "data": data, "workdir": workdir,
        "fmt_deg": fmt_deg, "SIGN_FULL": SIGN_FULL, "SIGN_GLYPH": SIGN_GLYPH,
        "positions_table": positions_table, "houses_table": houses_table,
        "balance_tables": balance_tables, "aspects_table": aspects_table,
        "overlay_table": overlay_table, "score_table": score_table,
        "svg_inline": lambda p: (s := Path(p).read_text())[s.index("<svg"):],
        "load_content": lambda slug: load_module(workdir / f"content_{slug}.py"),
    }

    for slug, subj in data["subjects"].items():
        mod_path = workdir / f"content_{slug}.py"
        if not mod_path.exists():
            print(f"skip {slug}: no {mod_path.name}")
            continue
        body = load_module(mod_path).build(ctx)
        (outdir / f"{slug}.html").write_text(page(f"Natal Chart — {subj['name']}", body))
        print(f"built {slug}.html")

    if "synastry" in data and (workdir / "content_synastry.py").exists():
        pair = data["synastry"]["pair"]
        names = [data["subjects"][s]["name"] for s in pair]
        body = load_module(workdir / "content_synastry.py").build(ctx)
        (outdir / "synastry.html").write_text(
            page(f"Synastry — {names[0]} & {names[1]}", body))
        print("built synastry.html")


if __name__ == "__main__":
    main()
