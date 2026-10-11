"""Rank the load-bearing facts in a natal chart, from chart-data.json alone.

Usage: python pipeline/facts.py work/<dir> [slug ...] [--top N]

Each detector reads the computed chart and emits facts with a salience score.
Weights follow the conventions in content_guide.md (luminaries > personal
planets > social > outer; angles and dignities count; concentrations and
absences are signatures). Facts whose planets are all covered by a higher
fact are dropped, so the top of the list is a set of distinct signatures.
"""
import json
import sys
from pathlib import Path

SIGNS = ["Ari", "Tau", "Gem", "Can", "Leo", "Vir", "Lib", "Sco", "Sag", "Cap", "Aqu", "Pis"]
ELEMENT = {s: e for s, e in zip(SIGNS, ["Fire", "Earth", "Air", "Water"] * 3, strict=True)}
MODALITY = {s: m for s, m in zip(SIGNS, ["Cardinal", "Fixed", "Mutable"] * 4, strict=True)}
PLANETS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
           "uranus", "neptune", "pluto"]
HOUSE_NUM = {n: i + 1 for i, n in enumerate(
    ["First", "Second", "Third", "Fourth", "Fifth", "Sixth", "Seventh",
     "Eighth", "Ninth", "Tenth", "Eleventh", "Twelfth"])}
ANGLES = {"ascendant": "Ascendant", "medium_coeli": "Midheaven",
          "descendant": "Descendant", "imum_coeli": "IC"}
TRAD_RULER = {"Ari": "mars", "Tau": "venus", "Gem": "mercury", "Can": "moon",
              "Leo": "sun", "Vir": "mercury", "Lib": "venus", "Sco": "mars",
              "Sag": "jupiter", "Cap": "saturn", "Aqu": "saturn", "Pis": "jupiter"}
DOMICILE = {"sun": ["Leo"], "moon": ["Can"], "mercury": ["Gem", "Vir"],
            "venus": ["Tau", "Lib"], "mars": ["Ari", "Sco"],
            "jupiter": ["Sag", "Pis"], "saturn": ["Cap", "Aqu"]}
EXALT = {"sun": "Ari", "moon": "Tau", "mercury": "Vir", "venus": "Pis",
         "mars": "Cap", "jupiter": "Can", "saturn": "Lib"}
WEIGHT = {"sun": 3, "moon": 3, "mercury": 2, "venus": 2, "mars": 2,
          "jupiter": 1.5, "saturn": 1.5, "uranus": 1, "neptune": 1, "pluto": 1}
ANGULAR = {1, 4, 7, 10}


def house(p):
    return HOUSE_NUM[p["house"].split("_")[0]]


def label(k):
    return k.replace("_", " ").title()


def detect(subj):
    pts = subj["points"]
    pl = {k: pts[k] for k in PLANETS}
    asc_sign = pts["ascendant"]["sign"]
    ruler = TRAD_RULER[asc_sign]
    facts = []

    def add(score, kind, text, planets):
        facts.append({"score": round(score, 1), "kind": kind, "text": text,
                      "planets": set(planets)})

    # Element and modality concentrations and absences (ten planets).
    for table, names in ((ELEMENT, ["Fire", "Earth", "Air", "Water"]),
                         (MODALITY, ["Cardinal", "Fixed", "Mutable"])):
        for n in names:
            members = [k for k, p in pl.items() if table[p["sign"]] == n]
            if not members:
                add(7, "missing", f"No planets in {n}", [])
            elif len(members) >= 5 and table is ELEMENT:
                bonus = 1 if ELEMENT[asc_sign] == n else 0
                add(3 * (len(members) - 3) + bonus, "majority",
                    f"{len(members)}/10 planets in {n}"
                    + (" (Ascendant too)" if bonus else ""), members)

    # Big three in one element.
    big3 = [pts["sun"]["sign"], pts["moon"]["sign"], asc_sign]
    if len({ELEMENT[s] for s in big3}) == 1:
        add(9, "big3", f"Sun, Moon and Ascendant all in {ELEMENT[big3[0]]}",
            ["sun", "moon", "ascendant"])

    # Stelliums by sign and by house; merged when they share 3+ planets.
    groups = []
    for key, fn in (("sign", lambda p: p["sign"]), ("house", house)):
        buckets = {}
        for k, p in pl.items():
            buckets.setdefault(fn(p), []).append(k)
        for where, members in buckets.items():
            if len(members) >= 3:
                groups.append((key, where, set(members)))
    used = set()
    for i, (key, where, members) in enumerate(groups):
        if i in used:
            continue
        desc = [f"{key} {where}"]
        allm = set(members)
        for j in range(i + 1, len(groups)):
            if len(members & groups[j][2]) >= 3:
                used.add(j)
                desc.append(f"{groups[j][0]} {groups[j][1]}")
                allm |= groups[j][2]
        score = 2 * len(allm) + (2 if len(desc) > 1 else 0)
        score += 2 if allm & {"sun", "moon", ruler} else 0
        add(score, "stellium", f"Stellium ({', '.join(desc)}): "
            + ", ".join(label(m) for m in sorted(allm, key=PLANETS.index)), allm)

    # Essential dignity, boosted on angular houses.
    for k, p in pl.items():
        if p["sign"] in DOMICILE.get(k, []):
            dig = "domicile"
        elif EXALT.get(k) == p["sign"]:
            dig = "exaltation"
        else:
            continue
        score = 2 * WEIGHT[k] + (2 if house(p) in ANGULAR else 0)
        add(score, "dignity", f"{label(k)} in {dig} ({p['sign']}), house {house(p)}", [k])

    # Planets within 5 degrees of an angle, grouped per angle.
    for ak, aname in ANGLES.items():
        hits = []
        for k, p in pl.items():
            d = abs((p["abs_pos"] - pts[ak]["abs_pos"] + 180) % 360 - 180)
            if d <= 5:
                hits.append((k, d))
        if hits:
            score = sum(2 * WEIGHT[k] + (5 - d) / 2 for k, d in hits)
            score += 2 if len(hits) > 1 else 0
            add(score, "angle", f"On the {aname}: " + ", ".join(
                f"{label(k)} ({d:.1f}°)" for k, d in hits), [k for k, _ in hits])

    # Chart ruler placement.
    rp = pl[ruler]
    score = 4 + (2 if house(rp) in ANGULAR | {12} else 0)
    add(score, "ruler", f"Chart ruler {label(ruler)} ({asc_sign} rising) in "
        f"{rp['sign']}, house {house(rp)}", [ruler])

    # Luminary in the house that naturally matches its sign (Aries=1 ... Pisces=12).
    for k in ("sun", "moon"):
        p = pl[k]
        if SIGNS.index(p["sign"]) + 1 == house(p):
            add(4, "resonance", f"{label(k)} in {p['sign']} in its natural house {house(p)}", [k])

    # Tight major aspects (orb under 2°) between luminaries, personal planets, angles.
    core = {"Sun", "Moon", "Mercury", "Venus", "Mars", "Ascendant", "Medium_Coeli"}
    major = {"conjunction", "opposition", "trine", "square", "sextile"}
    for a in subj["aspects"]:
        if (a["aspect"] in major and a["p1_name"] in core and a["p2_name"] in core
                and a["orbit"] < 2):
            names = [a["p1_name"].lower(), a["p2_name"].lower()]
            add(5 - 1.5 * a["orbit"], "aspect",
                f"{a['p1_name']} {a['aspect']} {a['p2_name']} ({a['orbit']:.1f}°)",
                [n for n in names if n in PLANETS])

    facts.sort(key=lambda f: -f["score"])
    kept, covered = [], set()
    for f in facts:
        if f["planets"] and f["planets"] <= covered:
            continue
        kept.append(f)
        covered |= f["planets"]
    return kept


def main(argv):
    top = 6
    if "--top" in argv:
        top = int(argv[argv.index("--top") + 1])
        del argv[argv.index("--top"):argv.index("--top") + 2]
    workdir = Path(argv[0])
    data = json.loads((workdir / "chart-data.json").read_text())
    slugs = argv[1:] or list(data["subjects"])
    for slug in slugs:
        print(f"== {slug}")
        for i, f in enumerate(detect(data["subjects"][slug])[:top], 1):
            print(f"{i:2}. [{f['score']:4}] {f['kind']:9} {f['text']}")


if __name__ == "__main__":
    main(sys.argv[1:])
