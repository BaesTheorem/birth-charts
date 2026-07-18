"""Compute chart data and themed wheel SVGs for a work directory.

Usage: python pipeline/compute.py work/<dir>

Reads work/<dir>/subjects.yaml:

    subjects:
      - slug: alexander
        name: Alexander
        year: 1994
        month: 5
        day: 29
        hour: 1        # 24h local time
        minute: 27
        city: San Antonio
        nation: US
        lat: 29.4167
        lng: -98.5
        tz: America/Chicago
      - slug: gabrielle
        ...
    synastry: [alexander, gabrielle]   # optional pair

Writes into the work dir: chart-data.json, wheel-<slug>.svg, and (if a pair is
declared) synastry-wheel.svg + synastry-grid.svg, all restyled with theme/elegant.css.
"""
import json
import re
import sys
from pathlib import Path

import yaml
from kerykeion import AstrologicalSubject, KerykeionChartSVG, NatalAspects, SynastryAspects
from kerykeion.relationship_score_factory import RelationshipScoreFactory

REPO = Path(__file__).resolve().parent.parent
THEME_CSS = (REPO / "theme" / "elegant.css").read_text()

POINTS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
          "uranus", "neptune", "pluto", "chiron", "mean_lilith", "true_node",
          "ascendant", "medium_coeli", "descendant", "imum_coeli"]
HOUSES = ["first_house", "second_house", "third_house", "fourth_house",
          "fifth_house", "sixth_house", "seventh_house", "eighth_house",
          "ninth_house", "tenth_house", "eleventh_house", "twelfth_house"]


def make_subject(cfg):
    return AstrologicalSubject(
        name=cfg["name"], year=cfg["year"], month=cfg["month"], day=cfg["day"],
        hour=cfg["hour"], minute=cfg["minute"],
        city=cfg.get("city", ""), nation=cfg.get("nation", "US"),
        lng=cfg["lng"], lat=cfg["lat"], tz_str=cfg["tz"], online=False)


def dump_subject(s):
    import warnings
    out = {"name": s.name, "julian_day": s.julian_day,
           "iso_utc": str(s.iso_formatted_utc_datetime),
           "local": str(s.iso_formatted_local_datetime),
           "lunar_phase": s.lunar_phase.model_dump() if s.lunar_phase else None}
    pts = {}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for p in POINTS:
            obj = getattr(s, p, None)
            if obj is None:
                continue
            d = obj.model_dump()
            pts[p] = {k: d.get(k) for k in
                      ("name", "quality", "element", "sign", "sign_num", "position",
                       "abs_pos", "emoji", "house", "retrograde")}
    out["points"] = pts
    out["houses"] = {}
    for h in HOUSES:
        obj = getattr(s, h, None)
        if obj is not None:
            d = obj.model_dump()
            out["houses"][h] = {k: d.get(k) for k in ("name", "sign", "position", "abs_pos")}
    return out


def dump_aspects(aspects_list):
    return [a.model_dump() if hasattr(a, "model_dump") else dict(a) for a in aspects_list]


THEME_BLOCK = re.compile(r"(<style kr:node='Theme_Colors_Tag'>).*?(</style>)", re.S)

# Kerykeion draws each zodiac glyph in a 32x32 symbol box slightly larger than the
# zodiac band, so the glyphs collide with the ring lines. Shrink each one in place,
# scaling around the glyph's own center (use x/y is the symbol's top-left corner).
ZODIAC_SHRINK = 0.72
ZODIAC_USE = re.compile(
    r"<use x='([-\d.]+)' y='([-\d.]+)' xlink:href='#(Ari|Tau|Gem|Can|Leo|Vir|Lib|Sco|Sag|Cap|Aqu|Pis)' */>")


def shrink_zodiac_use(m):
    x, y, sign = float(m.group(1)), float(m.group(2)), m.group(3)
    s = ZODIAC_SHRINK
    tx, ty = (1 - s) * (x + 16), (1 - s) * (y + 16)
    return (f"<g transform='translate({tx:.3f},{ty:.3f}) scale({s})'>"
            f"<use x='{x}' y='{y}' xlink:href='#{sign}' /></g>")


def retheme(svg_path):
    svg = svg_path.read_text()
    svg = THEME_BLOCK.sub(lambda m: m.group(1) + "\n" + THEME_CSS + "\n" + m.group(2), svg, count=1)
    svg = ZODIAC_USE.sub(shrink_zodiac_use, svg)
    svg_path.write_text(svg)


def newest_svg(dirpath, before):
    files = set(dirpath.glob("*.svg")) - before
    assert len(files) == 1, f"expected one new svg, got {files}"
    return files.pop()


def make_wheels(workdir, subjects, pair):
    for slug, subj in subjects.items():
        before = set(workdir.glob("*.svg"))
        KerykeionChartSVG(subj, chart_type="Natal", new_output_directory=str(workdir),
                          theme="classic").makeWheelOnlySVG()
        f = newest_svg(workdir, before)
        f = f.rename(workdir / f"wheel-{slug}.svg")
        retheme(f)
    if pair:
        s1, s2 = subjects[pair[0]], subjects[pair[1]]
        before = set(workdir.glob("*.svg"))
        KerykeionChartSVG(s1, chart_type="Synastry", second_obj=s2,
                          new_output_directory=str(workdir), theme="classic").makeWheelOnlySVG()
        f = newest_svg(workdir, before).rename(workdir / "synastry-wheel.svg")
        retheme(workdir / "synastry-wheel.svg")
        before = set(workdir.glob("*.svg"))
        KerykeionChartSVG(s1, chart_type="Synastry", second_obj=s2,
                          new_output_directory=str(workdir), theme="classic").makeAspectGridOnlySVG()
        newest_svg(workdir, before).rename(workdir / "synastry-grid.svg")
        retheme(workdir / "synastry-grid.svg")


def main():
    workdir = Path(sys.argv[1]).resolve()
    cfg = yaml.safe_load((workdir / "subjects.yaml").read_text())
    subjects = {c["slug"]: make_subject(c) for c in cfg["subjects"]}
    slug_cfg = {c["slug"]: c for c in cfg["subjects"]}
    pair = cfg.get("synastry")

    data = {"subjects": {}, "config": slug_cfg}
    for slug, subj in subjects.items():
        data["subjects"][slug] = dump_subject(subj)
        data["subjects"][slug]["aspects"] = dump_aspects(NatalAspects(subj).relevant_aspects)
    if pair:
        s1, s2 = subjects[pair[0]], subjects[pair[1]]
        data["synastry"] = {
            "pair": pair,
            "aspects": dump_aspects(SynastryAspects(s1, s2).relevant_aspects),
        }
        try:
            score = RelationshipScoreFactory(s1.model(), s2.model()).get_relationship_score()
            sd = score.model_dump()
            data["synastry"]["score"] = {
                "value": sd["score_value"], "description": sd["score_description"],
                "is_destiny_sign": sd["is_destiny_sign"],
                "breakdown": sd["score_breakdown"], "aspects": sd["aspects"]}
        except Exception as e:
            data["synastry"]["score"] = {"error": str(e)}

    (workdir / "chart-data.json").write_text(json.dumps(data, indent=1, default=str))
    make_wheels(workdir, subjects, pair)

    for slug, s in subjects.items():
        print(f"{slug}: Sun {s.sun.sign} {s.sun.position:.2f} | Moon {s.moon.sign} "
              f"{s.moon.position:.2f} | ASC {s.first_house.sign} {s.first_house.position:.2f}")
    if pair:
        sc = data["synastry"]["score"]
        print(f"synastry aspects: {len(data['synastry']['aspects'])}, "
              f"score: {sc.get('value')} ({sc.get('description', sc.get('error'))})")


if __name__ == "__main__":
    main()
