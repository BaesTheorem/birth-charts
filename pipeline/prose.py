"""The written layer on top of an --auto packet: brief a writer, then check the writing.

    python pipeline/prose.py brief work/<dir> <slug>   # facts + rules + JSON shape
    python pipeline/prose.py check work/<dir> <slug>   # exit 1 on ungrounded claims

The writer (a person, or the assistant running this repo) saves
work/<dir>/prose_<slug>.json. On the next --auto build, delineate.py uses its
signatures, lead and synthesis in place of the rule-table versions, but only
if `check` passes: every "X in Sign", "X in the Nth house", "X <aspect> Y" and
element count in the text has to match chart-data.json.
"""
import json
import re
import sys
from pathlib import Path

import facts

SIGN_FULL = {"Ari": "Aries", "Tau": "Taurus", "Gem": "Gemini", "Can": "Cancer",
             "Leo": "Leo", "Vir": "Virgo", "Lib": "Libra", "Sco": "Scorpio",
             "Sag": "Sagittarius", "Cap": "Capricorn", "Aqu": "Aquarius", "Pis": "Pisces"}
FULL_SIGN = {v: k for k, v in SIGN_FULL.items()}
POINTS = {"Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
          "Mars": "mars", "Jupiter": "jupiter", "Saturn": "saturn", "Uranus": "uranus",
          "Neptune": "neptune", "Pluto": "pluto", "Chiron": "chiron",
          "North Node": "true_node", "Lilith": "mean_lilith", "Ascendant": "ascendant",
          "Midheaven": "medium_coeli", "Descendant": "descendant", "IC": "imum_coeli"}
DATA_NAME = {"sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus",
             "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn",
             "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto",
             "chiron": "Chiron", "true_node": "True_North_Lunar_Node",
             "mean_lilith": "Mean_Lilith", "ascendant": "Ascendant",
             "medium_coeli": "Medium_Coeli", "descendant": "Descendant",
             "imum_coeli": "Imum_Coeli"}
ASPECT_WORDS = {"conjunct": "conjunction", "conjunction": "conjunction",
                "conjoins": "conjunction", "opposite": "opposition",
                "opposition": "opposition", "opposes": "opposition", "trine": "trine",
                "trines": "trine", "square": "square", "squares": "square",
                "sextile": "sextile", "sextiles": "sextile"}
ORDINALS = {w: i + 1 for i, w in enumerate(
    ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth",
     "ninth", "tenth", "eleventh", "twelfth"])}
NUMBERS = {w: i for i, w in enumerate(
    ["no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
     "ten"])}
ELEMENTS = ("fire", "earth", "air", "water")

POINT_RE = "|".join(sorted(map(re.escape, POINTS), key=len, reverse=True))
SIGN_RE = "|".join(FULL_SIGN)
HOUSE_RE = r"(\d{1,2})(?:st|nd|rd|th)|(" + "|".join(ORDINALS) + ")"
VERB = r"(?:\s+(?:is|was|sits|lies|falls|stands|placed|sitting|lying))?"
STRICT_SIGN = re.compile(rf"\b({POINT_RE})\b{VERB}\s+in\s+({SIGN_RE})\b")
STRICT_HOUSE = re.compile(
    rf"\b({POINT_RE})\b(?:\s+in\s+({SIGN_RE}))?{VERB}\s+in\s+the\s+(?:{HOUSE_RE})[\s-]house",
    re.I)
STRICT_ASPECT = re.compile(
    rf"\b({POINT_RE})\s+(?:is\s+|sits\s+)?(" + "|".join(ASPECT_WORDS) + r")\s+"
    rf"(?:to\s+|with\s+)?(?:the\s+)?({POINT_RE})\b")
COUNT = re.compile(r"\b(\d+|" + "|".join(NUMBERS) + r")\b(?:\s+of\s+the\s+(?:ten|10))?\s+"
                   r"planets?\s+(?:\w+\s+){0,2}in\s+(?:the\s+)?(" + "|".join(ELEMENTS) + ")",
                   re.I)


def subject(workdir, slug):
    data = json.loads((Path(workdir) / "chart-data.json").read_text())
    return data["subjects"][slug]


def house_of(p):
    return facts.house(p)


def sentences(text):
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", " ".join(text.split())) if s.strip()]


def check_text(subj, text):
    """Return a list of (sentence, problem) for claims that contradict the chart."""
    pts = subj["points"]
    aspects = {(a["p1_name"], a["p2_name"], a["aspect"]) for a in subj["aspects"]}
    problems = []
    for s in sentences(text):
        for name, sign in STRICT_SIGN.findall(s):
            key = POINTS[name]
            if key in pts and pts[key]["sign"] != FULL_SIGN[sign]:
                problems.append((s, f"{name} is in {SIGN_FULL[pts[key]['sign']]}, not {sign}"))
        for m in STRICT_HOUSE.finditer(s):
            name = next(n for n in POINTS if n.lower() == m.group(1).lower())
            key = POINTS[name]
            n = int(m.group(3)) if m.group(3) else ORDINALS[m.group(4).lower()]
            if key in pts and key not in ("ascendant", "medium_coeli", "descendant",
                                          "imum_coeli") and house_of(pts[key]) != n:
                problems.append((s, f"{name} is in house {house_of(pts[key])}, not {n}"))
        # Aspects, only in the explicit "X squares Y" form. Looser matching
        # misreads sentences whose subject is implied ("a trine to Uranus").
        for x, word, y in STRICT_ASPECT.findall(s):
            asp = ASPECT_WORDS[word.lower()]
            pa, pb = DATA_NAME[POINTS[x]], DATA_NAME[POINTS[y]]
            if x != y and (pa, pb, asp) not in aspects and (pb, pa, asp) not in aspects:
                problems.append((s, f"no {asp} between {x} and {y} in the chart"))
        for num, elem in COUNT.findall(s):
            n = int(num) if num.isdigit() else NUMBERS[num.lower()]
            real = sum(1 for k in facts.PLANETS
                       if facts.ELEMENT[pts[k]["sign"]].lower() == elem.lower())
            if n != real:
                problems.append((s, f"{real} planets are in {elem}, not {n}"))
    return problems


def prose_text(prose):
    parts = [f"{x['title']} {x['text']}" for x in prose.get("signatures", [])]
    parts.append(prose.get("lead", ""))
    parts += prose.get("synthesis", [])
    return " ".join(parts)


def load(workdir, slug):
    path = Path(workdir) / f"prose_{slug}.json"
    if not path.exists():
        return None
    prose = json.loads(path.read_text())
    for k in ("signatures", "lead", "synthesis"):
        if k not in prose:
            raise ValueError(f"{path.name}: missing key {k!r}")
    if len(prose["signatures"]) != 3:
        raise ValueError(f"{path.name}: need exactly 3 signatures")
    return prose


def brief(workdir, slug):
    subj = subject(workdir, slug)
    pts = subj["points"]
    lines = [f"# Writing brief: {subj['name']}", "",
             "Write the three signatures, the one-line lead and the synthesis for this "
             "natal packet. The rest of the packet is generated from rule tables.", "",
             "## Ranked signatures (from pipeline/facts.py; use the top three unless "
             "you have a reason)", ""]
    for i, f in enumerate(facts.detect(subj)[:8], 1):
        lines.append(f"{i}. [{f['score']}] {f['text']}")
    lines += ["", "## Placements", ""]
    for k in DATA_NAME:
        if k in pts:
            p = pts[k]
            r = " (retrograde)" if p.get("retrograde") else ""
            lines.append(f"- {POINTS_INV[k]}: {SIGN_FULL[p['sign']]} {p['position']:.1f}°, "
                         f"house {house_of(p)}{r}")
    lines += ["", "## Tightest major aspects", ""]
    major = [a for a in subj["aspects"] if a["aspect"] in set(ASPECT_WORDS.values())]
    shown = [a for a in sorted(major, key=lambda a: a["orbit"])
             if a["p1_name"] in DISPLAY and a["p2_name"] in DISPLAY]
    for a in shown[:15]:
        lines.append(f"- {DISPLAY[a['p1_name']]} {a['aspect']} {DISPLAY[a['p2_name']]} "
                     f"({a['orbit']:.1f}°)")
    phase = subj["lunar_phase"]["moon_phase_name"]
    night = house_of(pts["sun"]) <= 6
    lines += ["", f"Sect: {'night' if night else 'day'} chart. Lunar phase: {phase}.", "",
              "## Rules", "",
              "- Ground every claim in the data above: name the placement, house or orb.",
              "- Synthesis means connecting placements (how the Moon square Mars plays out "
              "given the 12th-house Moon), not listing them again.",
              "- Plain language; translate each technical term the first time.",
              "- Honest, not fatalistic. Include what takes work. No flattery.",
              "- No em dashes. No hype adverbs. Do not stack three-item lists.",
              "- Use the person's name or 'they'; do not assume pronouns.",
              "- Do not mention any other person or chart.", "",
              "## Output", "",
              f"Save as {Path(workdir) / f'prose_{slug}.json'}:", "",
              "```json",
              json.dumps({"signatures": [{"title": "Short bold title.",
                                          "text": "Two or three sentences."}] * 3,
                          "lead": "One sentence, no final period.",
                          "synthesis": ["Paragraph.", "Paragraph.", "Paragraph."]},
                         indent=2),
              "```", "",
              f"Then run: python pipeline/prose.py check {workdir} {slug}",
              f"and rebuild: python make.py {workdir} --auto"]
    return "\n".join(lines)


POINTS_INV = {v: k for k, v in POINTS.items()}
# Data names to the names the checker reads; the Descendant, IC and South Node
# only mirror the Ascendant, Midheaven and North Node, so the brief leaves them out.
DISPLAY = {DATA_NAME[k]: POINTS_INV[k] for k in DATA_NAME
           if k not in ("descendant", "imum_coeli")}


def main(argv):
    if len(argv) != 3 or argv[0] not in ("brief", "check"):
        sys.exit(__doc__)
    mode, workdir, slug = argv
    if mode == "brief":
        print(brief(workdir, slug))
        return
    prose = load(workdir, slug)
    if prose is None:
        sys.exit(f"no prose_{slug}.json in {workdir}")
    problems = check_text(subject(workdir, slug), prose_text(prose))
    for s, why in problems:
        print(f"UNGROUNDED: {why}\n    in: {s}")
    if problems:
        sys.exit(1)
    print(f"OK: prose_{slug}.json matches the chart")


if __name__ == "__main__":
    main(sys.argv[1:])
