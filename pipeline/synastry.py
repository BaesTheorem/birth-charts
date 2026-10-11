"""Rank and write a synastry packet from chart data alone, with no LLM.

    python pipeline/synastry.py work/<dir>     # print the ranked contacts

build.py uses build(ctx) for the pair when run with --auto and there is no
content_synastry.py. Ranking follows content_guide.md: luminary contacts first,
then Venus/Saturn (durability), Jupiter/Nodes (growth), Mars/Pluto (friction),
then angles. Within a group, the tighter orb wins.

Ownership: in data["synastry"]["aspects"], p1 belongs to pair[0] and p2 to
pair[1]. Every function here goes through contacts(), which asserts that, so a
swapped pair fails loudly instead of printing every sentence backwards.
"""
import json
import sys
from pathlib import Path

import delineate as dl
import facts
import prose

TIER = {"sun": 3, "moon": 3, "mercury": 2, "venus": 2, "mars": 2, "ascendant": 2,
        "jupiter": 1.5, "saturn": 1.5, "true_node": 1.5, "medium_coeli": 1.5,
        "uranus": 1, "neptune": 1, "pluto": 1, "chiron": 1, "mean_lilith": 1}
LUM = {"sun", "moon"}
CORE = {"sun", "moon", "mercury", "venus", "mars", "ascendant"}
GROUPS = [  # (label, test on the two point keys)
    ("luminaries", lambda a, b: a in LUM and b in LUM),
    ("luminary-ascendant", lambda a, b: {a, b} & LUM and {a, b} & {"ascendant"}),
    ("durability", lambda a, b: {a, b} & {"venus", "saturn"} and {a, b} & CORE),
    ("growth", lambda a, b: {a, b} & {"jupiter", "true_node"} and {a, b} & CORE),
    ("friction", lambda a, b: {a, b} & {"mars", "pluto"} and {a, b} & CORE),
    ("angles", lambda a, b: {a, b} & {"ascendant", "medium_coeli"}),
]
CHANNELS = [  # (heading, planet, one-line frame)
    ("Words and minds", "mercury", "Mercury contacts show how easily the two of them "
     "talk, plan and argue."),
    ("Love and affection", "venus", "Venus contacts show what each person finds lovable "
     "in the other and how affection moves."),
    ("Desire and drive", "mars", "Mars contacts show chemistry and conflict, which often "
     "come from the same place."),
    ("Growth, luck and belief", "jupiter", "Jupiter contacts show where each person makes "
     "the other larger, sometimes past what is wise."),
    ("Commitment and structure", "saturn", "Saturn contacts are the glue and the weight: "
     "they make things last and they make things heavy."),
    ("Depth, wildness and healing", ("pluto", "chiron", "mean_lilith"), "Pluto, Chiron "
     "and Lilith contacts reach the parts of a person that are not on display."),
    ("The nodal axis", "true_node", "Contacts to the North Node are read as a direction: "
     "what the relationship helps each person grow toward."),
]
BANDS = [(0, 5, "Minimal"), (5, 10, "Medium"), (10, 15, "Important"),
         (15, 20, "Very important"), (20, 30, "Exceptional"), (30, 999, "Rare exceptional")]
HARD = {"square", "opposition"}
HEAVY = {"saturn", "mars", "pluto"}


def partner_house(abs_pos, houses):
    cusps = [houses[k]["abs_pos"] for k in
             ["first_house", "second_house", "third_house", "fourth_house", "fifth_house",
              "sixth_house", "seventh_house", "eighth_house", "ninth_house", "tenth_house",
              "eleventh_house", "twelfth_house"]]
    for i in range(12):
        a, b = cusps[i], cusps[(i + 1) % 12]
        if (a <= abs_pos < b) if a <= b else (abs_pos >= a or abs_pos < b):
            return i + 1
    return None


def group_of(a, b):
    for i, (_, test) in enumerate(GROUPS):
        if test(a, b):
            return i
    return len(GROUPS)


def contacts(data):
    """Synastry aspects as dicts with owner slugs and point keys, ranked."""
    pair = data["synastry"]["pair"]
    names = [data["subjects"][s]["name"] for s in pair]
    out = []
    for a in data["synastry"]["aspects"]:
        if a["aspect"] not in dl.ASPECT:
            continue
        k1, k2 = dl.NAME_TO_KEY.get(a["p1_name"]), dl.NAME_TO_KEY.get(a["p2_name"])
        if not k1 or not k2:
            continue
        if a["orbit"] > (8 if {k1, k2} & LUM else 6):  # conventional synastry orbs
            continue
        if "p1_owner" in a:
            assert (a["p1_owner"], a["p2_owner"]) == tuple(names), \
                f"aspect owners {a['p1_owner']}/{a['p2_owner']} do not match pair {names}"
        out.append({"a": pair[0], "ka": k1, "b": pair[1], "kb": k2,
                    "aspect": a["aspect"], "orb": a["orbit"], "group": group_of(k1, k2),
                    "weight": TIER.get(k1, 1) * TIER.get(k2, 1)})
    out.sort(key=lambda c: (c["group"], c["orb"]))
    return out


def overlays(data):
    """Each owner's planets grouped by the partner house they land in, ranked."""
    pair = data["synastry"]["pair"]
    groups = []
    for owner, partner in (pair, pair[::-1]):
        o, p = data["subjects"][owner], data["subjects"][partner]
        by_house = {}
        for k in facts.PLANETS:
            h = partner_house(o["points"][k]["abs_pos"], p["houses"])
            by_house.setdefault(h, []).append(k)
        for h, ks in by_house.items():
            score = sum(TIER[k] for k in ks) + (1 if h in (1, 4, 7, 10) else 0)
            score += 1 if h in (5, 8) and {"venus", "mars"} & set(ks) else 0
            groups.append({"owner": owner, "partner": partner, "house": h,
                           "planets": ks, "score": score})
    groups.sort(key=lambda g: -g["score"])
    return groups


class Pair:
    def __init__(self, ctx):
        self.ctx = ctx
        self.data = ctx["data"]
        self.pair = self.data["synastry"]["pair"]
        self.subj = {s: self.data["subjects"][s] for s in self.pair}
        self.name = {s: self.subj[s]["name"] for s in self.pair}
        self.contacts = contacts(self.data)
        self.overlays = overlays(self.data)
        self.framed = set()
        self.used = set()

    # Phrases -------------------------------------------------------------

    def pt(self, slug, key, sign=False):
        p = self.subj[slug]["points"][key]
        s = f"{self.name[slug]}'s {dl.POINT[key][0]}"
        return f"{s} in {self.ctx['SIGN_FULL'][p['sign']]}" if sign else s

    def sentence(self, c, signs=False):
        _, verb, frame = dl.ASPECT[c["aspect"]]
        line = (f"{self.pt(c['a'], c['ka'], signs)} ({dl.POINT[c['ka']][2]}) and "
                f"{self.pt(c['b'], c['kb'], signs)} ({dl.POINT[c['kb']][2]}) {verb}: "
                f"{dl.article(c['aspect'])} {c['aspect']} with an orb of {c['orb']:.1f}°.")
        if c["aspect"] not in self.framed:
            self.framed.add(c["aspect"])
            line += " " + frame
        return line

    def key(self, c):
        return (c["ka"], c["kb"], c["aspect"])

    def entry(self, c, signs=True):
        self.used.add(self.key(c))
        g = dl.ASPECT[c["aspect"]][0]
        return (f'<div class="aspect-entry"><div class="asp-line">{self.pt(c["a"], c["ka"])} '
                f'<span class="g">{g}</span> {self.pt(c["b"], c["kb"])} '
                f'<span class="orb">{c["aspect"]} · {c["orb"]:.1f}°</span></div>'
                f"<p>{self.sentence(c, signs)}</p></div>")

    # Sections ------------------------------------------------------------

    def headline(self):
        top = [c for c in self.contacts if c["group"] == 0][:4]
        if len(top) < 2:
            top += [c for c in self.contacts if c["group"] in (1, 2)][:3 - len(top)]
        return top

    def elements(self):
        count = {}
        for s in self.pair:
            pts = self.subj[s]["points"]
            count[s] = {e: sum(1 for k in facts.PLANETS
                               if facts.ELEMENT[pts[k]["sign"]] == e)
                        for e in ("Fire", "Earth", "Air", "Water")}
        a, b = self.pair
        lines = []
        for e in ("Fire", "Earth", "Air", "Water"):
            ca, cb = count[a][e], count[b][e]
            if (ca >= 4 and cb <= 1) or (cb >= 4 and ca <= 1):
                hi, lo = (a, b) if ca > cb else (b, a)
                lines.append(f"{self.name[hi]} has {max(ca, cb)} planets in {e.lower()} "
                             f"and {self.name[lo]} has {min(ca, cb)}: {self.name[hi]} "
                             f"supplies the {dl.ELEMENT_NOTE[e]} that {self.name[lo]}'s "
                             "chart is short of.")
            elif ca >= 3 and cb >= 3:
                lines.append(f"Both charts are strong in {e.lower()} ({ca} and {cb} "
                             f"planets), which gives common ground in "
                             f"{dl.ELEMENT_NOTE[e]}.")
        if not lines:
            lines.append("The two charts have similar elemental balances, so neither "
                         "person mainly supplies what the other lacks.")
        return lines

    def score_section(self):
        sc = self.data["synastry"]["score"]
        val = sc["value"]
        rows = "".join(
            f"<tr><td class='num'>{f'{lo}–{hi}' if hi < 999 else f'{lo}+'}</td><td>"
            + (f"<b>{band} ← this pairing</b>" if lo <= val < hi else band) + "</td></tr>"
            for lo, hi, band in BANDS)
        earned = [r["description"] for r in sc["breakdown"]]
        a, b = (self.name[s] for s in self.pair)
        dest = ("Both Suns share a modality, which adds the destiny-sign bonus."
                if sc.get("is_destiny_sign") else
                "There is no destiny-sign bonus: the two Suns are in different modalities.")
        reading = (f"The pairing scores {val}, in the {sc['description']} band. "
                   + (f"The points came from: {', '.join(earned)}. " if earned else
                      "No item on the checklist scored. ")
                   + dest + " The method ignores Venus-Saturn, the Nodes, the house "
                   "overlays and every hard aspect outside its list, so read the rest of "
                   "this packet before you read much into the number.")
        return f"""
<section class="pb">
<h2><span class="no">Part Two</span>The Discepolo Scorecard</h2>
<p class="lead">Ciro Discepolo's synastry test scores a short checklist of classical bond
signatures instead of weighing every contact. Each item found earns points, and the total
places the pairing in a band.</p>
<p>The checklist counts aspects between the two Suns, contacts between one Sun and the other
Moon, contacts from either Sun or Moon to the other Ascendant, Venus-Mars contacts, and a
five-point bonus when both Suns share a modality. Sun-Sun hard aspects and Sun-Moon
conjunctions score 8, or 11 at an orb of 2° or less. Everything else on the list scores 4.</p>
<h3>What this pairing scored</h3>
{self.ctx["score_table"](sc)}
<p class="footer-note" style="margin-top:0; border-top:0; padding-top:0;">In each row the
first-named point is {a}'s and the second is {b}'s.</p>
<div class="cols2">
<div><h3>The bands</h3>
<table class="data"><thead><tr><th>Total</th><th>Band</th></tr></thead><tbody>{rows}
</tbody></table></div>
<div><h3>Reading it honestly</h3><p>{reading}</p></div>
</div>
</section>"""

    def channels(self):
        out = []
        for head, planet, frame in CHANNELS:
            keys = planet if isinstance(planet, tuple) else (planet,)
            cs = [c for c in self.contacts if (c["ka"] in keys or c["kb"] in keys)
                  and self.key(c) not in self.used
                  and (c["ka"] in CORE or c["kb"] in CORE or c["orb"] < 2)]
            cs = sorted(cs, key=lambda c: c["orb"])[:3]
            if cs:
                body = "".join(self.entry(c, signs=False) for c in cs)
            else:
                body = "<p>No close contacts in this channel.</p>"
            out.append(f"<h3>{head}</h3><p>{frame}</p>{body}")
        return "\n".join(out)

    def overlay_bullets(self, n=6):
        items = []
        for g in self.overlays[:n]:
            names = ", ".join(dl.POINT[k][0] for k in g["planets"])
            pl = "land" if len(g["planets"]) > 1 else "lands"
            items.append(
                f"<li><b>{self.name[g['owner']]}'s {names} {pl} in {self.name[g['partner']]}'s "
                f"{dl.ordinal(g['house'])} house.</b> {self.name[g['owner']]} activates "
                f"{self.name[g['partner']]}'s area of {dl.HOUSE_ARENA[g['house']]}.</li>")
        return "<ul>" + "".join(items) + "</ul>"

    def ledger(self):
        ranked = [c for c in self.contacts if c["group"] < 5]
        flows = [c for c in ranked if c["aspect"] in ("trine", "sextile")
                 or (c["aspect"] == "conjunction" and not {c["ka"], c["kb"]} & HEAVY)][:6]
        work = [c for c in ranked if c["aspect"] in HARD
                or (c["aspect"] == "conjunction" and {c["ka"], c["kb"]} & HEAVY)][:6]

        def li(c):
            return (f"<li>{self.pt(c['a'], c['ka'])} {c['aspect']} "
                    f"{self.pt(c['b'], c['kb'])} ({c['orb']:.1f}°)</li>")
        return ("<ul>" + "".join(map(li, flows)) + "</ul>",
                "<ul>" + "".join(map(li, work)) + "</ul>", flows, work)

    def synthesis(self):
        head = self.headline()
        _, _, flows, work = self.ledger()
        top_ov = self.overlays[0] if self.overlays else None
        a, b = (self.name[s] for s in self.pair)
        lead = (f"{a} and {b} meet first through "
                + (f"{self.pt(head[0]['a'], head[0]['ka'])} {head[0]['aspect']} "
                   f"{self.pt(head[0]['b'], head[0]['kb'])}" if head else "their elements"))
        paras = []
        lum = [c for c in head if c["group"] == 0]
        paras.append(
            f"The chart has {len(lum)} contact{'s' if len(lum) != 1 else ''} between the two "
            "people's Suns and Moons, the first thing astrologers look at in a pairing. "
            + ("When there are several, the bond tends to feel familiar early."
               if len(lum) >= 2 else "With few of them, the bond rests more on the other "
               "channels below."))
        paras.append(f"{len(flows)} of the closest personal contacts flow and {len(work)} "
                     "take work. " + " ".join(self.elements()))
        if top_ov:
            paras.append(
                f"The strongest overlay puts {self.name[top_ov['owner']]}'s "
                + ", ".join(dl.POINT[k][0] for k in top_ov["planets"])
                + f" in {self.name[top_ov['partner']]}'s {dl.ordinal(top_ov['house'])} house, "
                f"so {dl.HOUSE_ARENA[top_ov['house']]} is where this relationship shows most "
                f"in {self.name[top_ov['partner']]}'s life.")
        return lead, paras

    def build(self):
        c = self.ctx
        d = self.data
        a, b = self.pair
        na, nb = self.name[a], self.name[b]
        written = prose.load_synastry(c["workdir"])
        if written:
            bad = prose.check_synastry(d, prose.synastry_text(written))
            if bad:
                raise SystemExit("prose_synastry.json has ungrounded claims:\n" + "\n".join(
                    f"  {why}: {s}" for s, why in bad))
        wheel = c["svg_inline"](c["workdir"] / "synastry-wheel.svg")
        grid = c["svg_inline"](c["workdir"] / "synastry-grid.svg")
        strips = (f'<div class="cols2"><div class="b3col"><div class="who">{na}</div>'
                  f'{c["bigthree_strip"](self.subj[a])}</div><div class="b3col">'
                  f'<div class="who">{nb}</div>{c["bigthree_strip"](self.subj[b])}</div></div>')
        cfg = d["config"]

        def birth(s):
            loc = self.subj[s]["local"]
            return (f'<div class="birthdata">{self.name[s]} · {loc[:10]} · {loc[11:16]} local '
                    f'· {cfg[s].get("city", "")}</div>')
        head = self.headline()
        stats = "".join(
            f'<div><div class="lbl">{self.pt(h["a"], h["ka"])} · '
            f'{self.pt(h["b"], h["kb"])}</div><div class="val">'
            f'{dl.ASPECT[h["aspect"]][0]} {h["aspect"]}</div></div>' for h in head[:2])
        sc = d["synastry"]["score"]
        stats += (f'<div><div class="lbl">Discepolo score</div><div class="val">{sc["value"]} '
                  f'· {sc["description"]}</div></div>')
        lead, synth = self.synthesis()
        if written:
            lead, synth = written["lead"].rstrip("."), written["synthesis"]
        attraction = ""
        if written and written.get("attraction"):
            attraction = ('<section class="pb"><h2><span class="no">Extra</span>Attraction '
                          '&amp; Intimacy</h2>' + "".join(
                              f"<p>{p}</p>" for p in written["attraction"]) + "</section>")
        headline_html = "\n".join(self.entry(h) for h in head)
        channels = self.channels()
        flows_ul, work_ul, _, _ = self.ledger()
        method = ("Lead and synthesis written from a brief and checked against the chart "
                  "data; the rest assembled from rule tables." if written else
                  "Text assembled from rule tables, without a language model.")
        elements = "".join(f"<p>{x}</p>" for x in self.elements())
        return f"""
<div class="cover">
  <div class="kicker">Synastry · Relationship Astrology · Tropical Zodiac · Placidus Houses · Swiss Ephemeris</div>
  <h1>{na} &amp; {nb}</h1>
  {birth(a)}
  {birth(b)}
  {strips}
  <hr class="rule">
  <div class="bigthree">{stats}</div>
  <div class="wheelwrap synastry">{wheel}</div>
  <div class="foot">Inner wheel: {na} · Outer wheel: {nb}</div>
</div>

<section class="pb">
<h2><span class="no">Part One</span>How to Read This Chart</h2>
<p class="lead">A synastry chart lays one birth chart over the other and studies the angles
between them. Each contact is one channel of the relationship. No single aspect decides
anything; the pattern does.</p>
<p>Two kinds of evidence appear here. <b>Interaspects</b> are angles between one person's
planets and the other's: trines and sextiles flow, conjunctions fuse, and squares and
oppositions make friction and fascination. <b>House overlays</b> show where each person's
planets land in the other's houses, that is, which areas of life the other person
activates.</p>
<div class="callout"><div class="ttl">The elemental exchange</div>{elements}</div>
</section>
{self.score_section()}

<section class="pb">
<h2><span class="no">Part Three</span>The Headline Contacts</h2>
<p class="lead">Astrologers check contacts between the Suns and Moons first: they show how
who one person is meets what the other needs.</p>
{headline_html}
</section>

<section class="pb">
<h2><span class="no">Part Four</span>Channel by Channel</h2>
{channels}
</section>
{attraction}
<section class="pb">
<h2><span class="no">Part Five</span>House Overlays</h2>
<div class="cols2">
<div>{c["overlay_table"](self.subj[a], self.subj[b], na, nb)}</div>
<div>{c["overlay_table"](self.subj[b], self.subj[a], nb, na)}</div>
</div>
<h3>What stands out</h3>
{self.overlay_bullets()}
</section>

<section class="pb">
<h2><span class="no">Part Six</span>The Honest Ledger</h2>
<div class="cols2">
<div><h3>What flows</h3>{flows_ul}</div>
<div><h3>What takes work</h3>{work_ul}</div>
</div>
</section>

<section class="pb">
<h2><span class="no">Part Seven</span>Synthesis</h2>
<p class="lead">If the pairing were a single line: {lead}.</p>
{"".join(f"<p>{p}</p>" for p in synth)}
<p class="footer-note">Calculated with Swiss Ephemeris · Tropical zodiac · Placidus houses ·
Birth data as provided. {method} Astrology is offered here as a reflective language, not a
deterministic science; take what is useful.</p>
</section>

<section class="pb">
<h2><span class="no">Appendix</span>Aspect Grid &amp; Complete Aspect List</h2>
<div class="wheelwrap">{grid}</div>
{c["aspects_table"](d["synastry"]["aspects"], dual=True, names=(na, nb))}
</section>
"""


def build(ctx):
    return Pair(ctx).build()


def main(argv):
    data = json.loads((Path(argv[0]) / "chart-data.json").read_text())
    names = {s: data["subjects"][s]["name"] for s in data["synastry"]["pair"]}
    print("== headline-ranked contacts")
    for c in contacts(data)[:12]:
        print(f"  [{GROUPS[c['group']][0] if c['group'] < len(GROUPS) else 'other':18}] "
              f"{names[c['a']]}'s {dl.POINT[c['ka']][0]} {c['aspect']} "
              f"{names[c['b']]}'s {dl.POINT[c['kb']][0]} ({c['orb']:.1f}°)")
    print("== overlays")
    for g in overlays(data)[:6]:
        print(f"  [{g['score']}] {names[g['owner']]}'s "
              + ", ".join(dl.POINT[k][0] for k in g["planets"])
              + f" in {names[g['partner']]}'s house {g['house']}")


if __name__ == "__main__":
    main(sys.argv[1:])
