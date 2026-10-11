"""Write a complete natal packet body from chart data alone, with no LLM.

build.py uses this for any subject without a content_<slug>.py when run with
--auto. Every sentence comes from the keyword tables below plus the ranked
facts in facts.py, so each claim traces to a placement, a house or an orb.
The interpretive design (planet function + sign style + house arena) follows
Astrolog's interpreter; the wording here is our own.
"""
import facts

SIGN_STYLE = {
    "Ari": ("direct, fast and brave", "wants to start things and test itself"),
    "Tau": ("steady, sensual and patient", "wants security and things that last"),
    "Gem": ("curious, quick and talkative", "wants information and variety"),
    "Can": ("protective, tender and guided by memory", "wants safety and belonging"),
    "Leo": ("warm, proud and expressive", "wants to create and to be seen"),
    "Vir": ("precise, useful and self-critical", "wants to improve whatever it touches"),
    "Lib": ("diplomatic, fair and attuned to others", "wants balance and partnership"),
    "Sco": ("intense, private and loyal", "wants depth and the truth under the surface"),
    "Sag": ("candid, restless and hopeful", "wants meaning and wide horizons"),
    "Cap": ("disciplined, ambitious and dry", "wants structure and earned achievement"),
    "Aqu": ("independent, inventive and a little detached",
            "wants freedom and a better system"),
    "Pis": ("receptive, imaginative and compassionate",
            "wants connection to something larger than itself"),
}
HOUSE_ARENA = {
    1: "the self, the body and first impressions",
    2: "money, possessions and self-worth",
    3: "siblings, neighbors and everyday talk",
    4: "home, family and private life",
    5: "creativity, romance and play",
    6: "work routines, health and service",
    7: "partnership and one-to-one relationships",
    8: "intimacy, shared resources and transformation",
    9: "travel, higher learning and belief",
    10: "career, reputation and public direction",
    11: "friends, groups and hopes for the future",
    12: "solitude, the unconscious and what stays hidden",
}
POINT = {  # key: (display name, function phrase, short noun, glyph)
    "sun": ("Sun", "core identity and sense of purpose", "identity", "☉"),
    "moon": ("Moon", "emotional needs and instinctive reactions", "feelings", "☽"),
    "mercury": ("Mercury", "way of thinking, learning and talking", "mind", "☿"),
    "venus": ("Venus", "way of loving, valuing and enjoying", "affections", "♀"),
    "mars": ("Mars", "drive, desire and way of fighting", "drive", "♂"),
    "jupiter": ("Jupiter", "faith, generosity and appetite for growth", "optimism", "♃"),
    "saturn": ("Saturn", "discipline, fears and long commitments", "discipline", "♄"),
    "uranus": ("Uranus", "need for freedom and for breaks with convention",
               "independence", "♅"),
    "neptune": ("Neptune", "ideals, imagination and sensitivity", "imagination", "♆"),
    "pluto": ("Pluto", "relationship to power, depth and change", "intensity", "♇"),
    "chiron": ("Chiron", "deepest wound, and the skill it later teaches", "old wound", "⚷"),
    "true_node": ("North Node", "direction of growth in this life", "growth path", "☊"),
    "mean_lilith": ("Lilith", "refused, untamed part of the self", "wild edge", "⚸"),
    "medium_coeli": ("Midheaven", "public direction and vocation", "public aim", "MC"),
    "ascendant": ("Ascendant", "outward manner and approach to life", "self-presentation",
                  "AC"),
}
NAME_TO_KEY = {"Sun": "sun", "Moon": "moon", "Mercury": "mercury", "Venus": "venus",
               "Mars": "mars", "Jupiter": "jupiter", "Saturn": "saturn",
               "Uranus": "uranus", "Neptune": "neptune", "Pluto": "pluto",
               "Chiron": "chiron", "True_North_Lunar_Node": "true_node",
               "Mean_Lilith": "mean_lilith", "Ascendant": "ascendant",
               "Medium_Coeli": "medium_coeli"}
ASPECT = {  # name: (glyph, verb phrase, framing)
    "conjunction": ("☌", "fuse into one voice",
                    "It is hard to use one of these functions without the other."),
    "sextile": ("⚹", "cooperate when asked",
                "The help is real but it is an opportunity: it pays out when it is used."),
    "trine": ("△", "flow together with little effort",
              "This is a native talent, and the risk is to take it for granted."),
    "square": ("□", "rub against each other",
               "The friction forces action, and over time it builds real capacity."),
    "opposition": ("☍", "pull in opposite directions",
                   "The tension often shows up through other people first, and the work "
                   "is to hold both ends at once."),
}
JOY = {"saturn": 12, "jupiter": 11, "mars": 6, "sun": 9, "moon": 3, "venus": 5,
       "mercury": 1}
PHASE = {
    "New Moon": "a phase associated with instinct and fresh starts: people who act first "
                "and understand later",
    "Waxing Crescent": "a phase associated with effort against inertia: people who push "
                       "new things past their first resistance",
    "First Quarter": "a phase associated with decisive action: people who build under "
                     "pressure",
    "Waxing Gibbous": "a phase associated with refinement: people who improve and adjust "
                      "until a thing works",
    "Full Moon": "a phase associated with awareness through others: people who see "
                 "themselves most clearly in relationship",
    "Waning Gibbous": "a phase associated with sharing what has been learned: natural "
                      "explainers and teachers",
    "Last Quarter": "a phase associated with reorientation: people who outgrow old "
                    "structures and say so",
    "Waning Crescent": "a phase associated with release and vision: people who finish "
                       "cycles and prepare the ground for the next one",
}
ELEMENT_NOTE = {
    "Fire": "initiative, enthusiasm and the will to act",
    "Earth": "practical sense, patience and attention to the body",
    "Air": "ideas, conversation and a wide view",
    "Water": "feeling, memory and emotional attunement",
}
MODALITY_NOTE = {
    "Cardinal": "starting things", "Fixed": "sustaining things",
    "Mutable": "adapting things",
}
DIGNITY_NOTE = {
    "domicile": "its own sign, its strongest placement (called domicile)",
    "exaltation": "the sign of its exaltation, where it works at its best",
}
ORD = {1: "1st", 2: "2nd", 3: "3rd"}
MAJOR = set(ASPECT)
PERSONAL = {"sun", "moon", "mercury", "venus", "mars", "ascendant", "medium_coeli"}


def ordinal(n):
    return ORD.get(n, f"{n}th")


def article(word):
    return "an" if word[0].lower() in "aeiou" else "a"


def the(name):
    """'the Sun', 'the Midheaven', but bare 'Mars'."""
    return f"the {name}" if name in ("Sun", "Moon", "Midheaven", "North Node",
                                     "Ascendant") else name


def cap(s):
    return s[0].upper() + s[1:]


def detriment(key, sign):
    rulers = facts.DOMICILE.get(key, [])
    opp = {facts.SIGNS[(facts.SIGNS.index(s) + 6) % 12] for s in rulers}
    if sign in opp:
        return "detriment"
    ex = facts.EXALT.get(key)
    if ex and sign == facts.SIGNS[(facts.SIGNS.index(ex) + 6) % 12]:
        return "fall"
    return None


class Chart:
    def __init__(self, ctx, slug):
        self.ctx = ctx
        self.slug = slug
        self.d = ctx["data"]["subjects"][slug]
        self.cfg = ctx["data"]["config"][slug]
        self.name = self.d["name"]
        self.pts = self.d["points"]
        self.facts = facts.detect(self.d)
        self.framed = set()
        self.aspects = [a for a in self.d["aspects"] if a["aspect"] in MAJOR
                        and a["p1_name"] in NAME_TO_KEY and a["p2_name"] in NAME_TO_KEY]

    def sign_full(self, sign):
        return self.ctx["SIGN_FULL"][sign]

    def house(self, key):
        return facts.house(self.pts[key])

    def deg(self, key):
        return self.ctx["fmt_deg"](self.pts[key]["position"])

    def night(self):
        return self.house("sun") <= 6

    def ruler(self):
        return facts.TRAD_RULER[self.pts["ascendant"]["sign"]]

    def aspects_of(self, key):
        out = [a for a in self.aspects
               if key in (NAME_TO_KEY[a["p1_name"]], NAME_TO_KEY[a["p2_name"]])]
        return sorted(out, key=lambda a: a["orbit"])

    # Sentences -----------------------------------------------------------

    def sign_sentence(self, key):
        name, func, _, _ = POINT[key]
        style, motive = SIGN_STYLE[self.pts[key]["sign"]]
        sign = self.sign_full(self.pts[key]["sign"])
        return (f"{cap(the(name))} in {sign} describes {self.name}'s {func}. The style is "
                f"{style}, and it {motive}.")

    def house_sentence(self, key):
        h = self.house(key)
        return f"In the {ordinal(h)} house, this plays out in {HOUSE_ARENA[h]}."

    def condition_sentences(self, key):
        out = []
        p = self.pts[key]
        sign = self.sign_full(p["sign"])
        if p["sign"] in facts.DOMICILE.get(key, []):
            out.append(f"{sign} is {DIGNITY_NOTE['domicile']}, so this function is "
                       "easy to reach and hard to suppress.")
        elif facts.EXALT.get(key) == p["sign"]:
            out.append(f"{sign} is {DIGNITY_NOTE['exaltation']}.")
        elif (dt := detriment(key, p["sign"])):
            out.append(f"{sign} is the sign of this planet's {dt}, a placement where "
                       "it has to work harder and often learns more as a result.")
        if JOY.get(key) == self.house(key):
            out.append(f"The {ordinal(self.house(key))} house is also this planet's "
                       "traditional joy, the house where it was said to be most at home.")
        if p.get("retrograde") and key not in ("true_node", "mean_lilith"):
            out.append("It was retrograde at birth, so its themes tend to work inward "
                       "first and come out later, on its own schedule.")
        return out

    def aspect_sentence(self, a, subject_key=None, frame=True):
        k1, k2 = NAME_TO_KEY[a["p1_name"]], NAME_TO_KEY[a["p2_name"]]
        if subject_key == k2:
            k1, k2 = k2, k1
        _, verb, _ = ASPECT[a["aspect"]]
        n1, _, s1, _ = POINT[k1]
        n2, _, s2, _ = POINT[k2]
        line = (f"{cap(the(n1))} ({s1}) and {the(n2)} ({s2}) {verb}: "
                f"{article(a['aspect'])} {a['aspect']} with an orb of {a['orbit']:.1f}°.")
        return f"{line} {ASPECT[a['aspect']][2]}" if frame else line

    def aspect_run(self, aspects, key=None):
        """Aspect sentences; each aspect type's framing sentence appears once per packet."""
        out = []
        for a in aspects:
            out.append(self.aspect_sentence(a, key, frame=a["aspect"] not in self.framed))
            self.framed.add(a["aspect"])
        return " ".join(out)

    def fact_paragraph(self, f):
        d = f["data"]
        kind = f["kind"]
        if kind == "big3":
            return (f"All three in {d['name']}.",
                    f"Sun, Moon and Ascendant all sit in {d['name'].lower()} signs. "
                    f"The three most personal points of the chart agree, so "
                    f"{ELEMENT_NOTE[d['name']]} run through identity, feeling and outward "
                    "manner alike.")
        if kind == "majority":
            names = ", ".join(POINT[m][0] for m in d["members"])
            asc = " The Ascendant is in the same element." if d["asc"] else ""
            return (f"A {d['name'].lower()} majority.",
                    f"{len(d['members'])} of the ten planets ({names}) are in "
                    f"{d['name'].lower()} signs. {ELEMENT_NOTE[d['name']].capitalize()} "
                    f"are the chart's default settings.{asc}")
        if kind == "missing":
            if d["name"] in ELEMENT_NOTE:
                note = ELEMENT_NOTE[d["name"]]
            else:
                note = f"the energy of {MODALITY_NOTE[d['name']]}"
            return (f"No planets in {d['name'].lower()}.",
                    f"Not one of the ten planets is in a {d['name'].lower()} sign. "
                    f"{note.capitalize()} do not come built in here. They tend to arrive "
                    "through other people, or through effort and practice.")
        if kind == "stellium":
            names = ", ".join(POINT[m][0] for m in d["members"])
            parts = []
            for w in d["where"]:
                key, val = w.split(" ", 1)
                parts.append(self.sign_full(val) if key == "sign"
                             else f"the {ordinal(int(val))} house")
            arena = ""
            hs = [w for w in d["where"] if w.startswith("house")]
            if hs:
                arena = f", the house of {HOUSE_ARENA[int(hs[0].split()[1])]}"
            ruler = (" The chart ruler is one of them, which ties this cluster to the "
                     "whole personality." if self.ruler() in d["members"] else "")
            return (f"A cluster in {' and '.join(parts)}.",
                    f"{names} gather in {' and '.join(parts)}{arena}. Three or more planets "
                    "in one place is called a stellium: a concentration of energy that "
                    f"the rest of the chart organizes around.{ruler}")
        if kind == "dignity":
            n = POINT[d["planet"]][0]
            return (f"{n} in its strength.",
                    f"{n} is in {self.sign_full(d['sign'])}, "
                    f"{DIGNITY_NOTE[d['dignity']]}, in the {ordinal(d['house'])} house of "
                    f"{HOUSE_ARENA[d['house']]}. Its {POINT[d['planet']][1]} is one of the "
                    "most reliable assets in the chart.")
        if kind == "angle":
            hits = " and ".join(f"{POINT[k][0]} ({o:.1f}°)" for k, o in d["hits"])
            return (f"Planets on the {d['angle']}.",
                    f"{hits} sit within five degrees of the {d['angle']}, one of the four "
                    "angles of the chart. Planets on an angle are loud: their themes "
                    "show early and others notice them.")
        if kind == "ruler":
            n = POINT[d["planet"]][0]
            return ("The chart ruler.",
                    f"With {self.sign_full(d['asc_sign'])} rising, {n} rules the chart, "
                    f"and it sits in {self.sign_full(d['sign'])} in the "
                    f"{ordinal(d['house'])} house of {HOUSE_ARENA[d['house']]}. That house "
                    "is where the whole life tends to point.")
        if kind == "resonance":
            n = POINT[d["planet"]][0]
            return (f"The {n} at home in its house.",
                    f"The {n} is in {self.sign_full(d['sign'])} in the "
                    f"{ordinal(d['house'])} house, the house that matches that sign in the "
                    f"natural zodiac. Sign and house say the same thing twice: "
                    f"{HOUSE_ARENA[d['house']]}.")
        if kind == "aspect":
            a = {"p1_name": d["p1"], "p2_name": d["p2"], "aspect": d["aspect"],
                 "orbit": d["orb"]}
            return (f"{POINT[NAME_TO_KEY[d['p1']]][0]} {d['aspect']} "
                    f"{POINT[NAME_TO_KEY[d['p2']]][0]}.", self.aspect_sentence(a))
        return (f["text"], f["text"])

    # Sections ------------------------------------------------------------

    def entry(self, key, subtitle=""):
        p = self.pts[key]
        name, _, _, _ = POINT[key]
        sign = self.sign_full(p["sign"])
        glyph = self.ctx["SIGN_GLYPH"][p["sign"]]
        body = [self.sign_sentence(key)]
        if key != "medium_coeli":
            body.append(self.house_sentence(key))
        body += self.condition_sentences(key)
        asp = [a for a in self.aspects_of(key) if a["orbit"] < 4][:2]
        extra = self.aspect_run(asp, key)
        pos = f'<div class="pos">{subtitle}</div>' if subtitle else ""
        tag = (f"Midheaven {self.deg(key)}" if key == "medium_coeli"
               else f"{ordinal(self.house(key))} house · {self.deg(key)}")
        paras = f"<p>{' '.join(body)}</p>" + (f"<p>{extra}</p>" if extra else "")
        return (f'<div class="entry"><h3>{name} in {glyph} {sign} '
                f'<span class="tag">{tag}</span></h3>{pos}{paras}</div>')

    def rising_entry(self):
        asc = self.pts["ascendant"]
        style, motive = SIGN_STYLE[asc["sign"]]
        sign = self.sign_full(asc["sign"])
        glyph = self.ctx["SIGN_GLYPH"][asc["sign"]]
        r = self.ruler()
        return (f'<div class="entry"><h3>{glyph} {sign} Rising <span class="tag">Ascendant '
                f'{self.deg("ascendant")}</span></h3><div class="pos">The outward self · '
                f'first impressions · the body\'s style</div>'
                f"<p>The Ascendant is the sign rising on the eastern horizon at the minute of "
                f"birth. With {sign} rising, {self.name} meets the world in {article(style)} {style} "
                f"manner, "
                f"and the approach to new situations {motive}.</p>"
                f"<p>{sign} is ruled by {POINT[r][0]}, which makes {POINT[r][0]} the chart "
                f"ruler. It sits in {self.sign_full(self.pts[r]['sign'])} in the "
                f"{ordinal(self.house(r))} house, so the outward style steers toward "
                f"{HOUSE_ARENA[self.house(r)]}.</p></div>")

    def sect_paragraph(self):
        phase = self.d["lunar_phase"]["moon_phase_name"]
        if self.night():
            sect = ("This is a night chart: the Sun was below the horizon at birth. In "
                    "traditional astrology the Moon, not the Sun, leads a night chart, which "
                    f"gives the Moon in {self.sign_full(self.pts['moon']['sign'])} extra "
                    "weight.")
        else:
            sect = ("This is a day chart: the Sun was above the horizon at birth. The Sun "
                    "leads a day chart, so identity and purpose take the front seat.")
        return f"<p>{sect} The Moon was in its {phase.lower()} phase, {PHASE[phase]}.</p>"

    def balance_note(self):
        counts = {}
        for k in facts.PLANETS:
            m = facts.MODALITY[self.pts[k]["sign"]]
            counts[m] = counts.get(m, 0) + 1
        top = max(counts, key=lambda m: counts[m])
        return (f"Tallies count the ten planets (Sun through Pluto). The modality lead is "
                f"{top.lower()} ({counts[top]} of 10), a bias toward "
                f"{MODALITY_NOTE[top]}.")

    def headline_aspects(self, n=10):
        def weight(a):
            ks = {NAME_TO_KEY[a["p1_name"]], NAME_TO_KEY[a["p2_name"]]}
            return a["orbit"] - 1.5 * len(ks & PERSONAL)
        return sorted(self.aspects, key=weight)[:n]

    def aspect_entry(self, a):
        k1, k2 = NAME_TO_KEY[a["p1_name"]], NAME_TO_KEY[a["p2_name"]]
        g = ASPECT[a["aspect"]][0]
        return (f'<div class="aspect-entry"><div class="asp-line">{POINT[k1][3]} '
                f'{POINT[k1][0]} <span class="g">{g}</span> {POINT[k2][0]} {POINT[k2][3]} '
                f'<span class="orb">{a["aspect"]} · {a["orbit"]:.1f}°</span></div>'
                f"<p>{self.aspect_run([a])}</p></div>")

    def synthesis(self):
        top = self.facts[:3]
        lead = top[0]["text"] if top else ""
        heads = [self.fact_paragraph(f)[0].rstrip(".").lower() for f in top]
        hard = [a for a in self.headline_aspects(20)
                if a["aspect"] in ("square", "opposition")][:2]
        easy = [a for a in self.headline_aspects(20)
                if a["aspect"] in ("trine", "sextile")][:2]
        node = self.pts["true_node"]
        mc = self.pts["medium_coeli"]
        p1 = ("The chart rests on " + ", ".join(heads[:-1]) + f" and {heads[-1]}. "
              "Read the rest of this packet against those three; most of the "
              "individual placements either feed them or push against them.") if heads else ""
        p2 = f"What comes easily: {self.aspect_run(easy)}" if easy else ""
        p3 = f"What takes work: {self.aspect_run(hard)}" if hard else ""
        p4 = (f"Direction: the North Node in {self.sign_full(node['sign'])} in the "
              f"{ordinal(self.house('true_node'))} house points growth toward "
              f"{HOUSE_ARENA[self.house('true_node')]}, and the Midheaven in "
              f"{self.sign_full(mc['sign'])} sets a public aim that "
              f"{SIGN_STYLE[mc['sign']][1]}.")
        return lead, [p for p in (p1, p2, p3, p4) if p]

    def build(self):
        c = self.ctx
        d = self.d
        cfg = self.cfg
        elem_tbl, mode_tbl = c["balance_tables"](d)
        wheel = c["svg_inline"](c["workdir"] / f"wheel-{self.slug}.svg")
        local = d["local"]
        sigs = "".join(f"<p><b>{i}. {h}</b> {t}</p>" for i, (h, t) in
                       enumerate((self.fact_paragraph(f) for f in self.facts[:3]), 1))
        lead, synth = self.synthesis()
        four = "\n".join(self.entry(k) for k in
                         ["mercury", "venus", "mars", "jupiter", "saturn", "uranus",
                          "neptune", "pluto", "chiron", "true_node", "mean_lilith",
                          "medium_coeli"])
        asp = "\n".join(self.aspect_entry(a) for a in self.headline_aspects())
        return f"""
<div class="cover">
  <div class="kicker">Natal Chart · Tropical Zodiac · Placidus Houses · Swiss Ephemeris</div>
  <h1>{self.name}</h1>
  <div class="birthdata">{local[:10]} · {local[11:16]} local · {cfg.get("city", "")} ·
  {abs(cfg["lat"]):.2f}°{"N" if cfg["lat"] >= 0 else "S"}
  {abs(cfg["lng"]):.2f}°{"E" if cfg["lng"] >= 0 else "W"}</div>
  <hr class="rule">
  {c["bigthree_strip"](d)}
  <div class="wheelwrap">{wheel}</div>
  <div class="foot">{d["lunar_phase"]["moon_phase_name"]} Moon ·
  {"Night" if self.night() else "Day"} Birth</div>
</div>

<section class="pb">
<h2><span class="no">Part One</span>The Chart at a Glance</h2>
<p class="lead">Every symbol in this packet was calculated with the Swiss Ephemeris for the
exact minute and coordinates of birth. Positions use the tropical zodiac and Placidus houses,
the standard in modern Western practice.</p>
<div class="callout"><div class="ttl">Three signatures to hold onto</div>{sigs}</div>
<div class="cols2"><div>{elem_tbl}</div><div>{mode_tbl}</div></div>
<p class="footer-note">{self.balance_note()}</p>
<h3>{"Night" if self.night() else "Day"} birth and the lunar phase</h3>
{self.sect_paragraph()}
<h3>The chart ruler</h3>
<p>{self.fact_paragraph({"kind": "ruler", "text": "", "data": {
    "planet": self.ruler(), "sign": self.pts[self.ruler()]["sign"],
    "house": self.house(self.ruler()), "asc_sign": self.pts["ascendant"]["sign"]}})[1]}</p>
</section>

<section class="pb">
<h2><span class="no">Part Two</span>Positions &amp; Houses</h2>
<h3>Planetary positions</h3>
{c["positions_table"](d)}
<div class="cols2">
<div><h3>House cusps (Placidus)</h3>{c["houses_table"](d)}</div>
<div><h3>Reading the table</h3>
<p>℞ marks a planet that was retrograde, appearing to move backward from Earth's point of
view. Houses are the twelve arenas of life, counted from the Ascendant: the house tells you
<i>where</i> a planet's energy plays out, and the sign tells you <i>how</i>.</p>
<p>The angles (Ascendant, Midheaven, Descendant, IC) are the chart's compass points: self,
public direction, partnership and roots.</p></div>
</div>
</section>

<section class="pb">
<h2><span class="no">Part Three</span>The Big Three</h2>
{self.entry("sun", "Core identity · vitality · purpose")}
{self.entry("moon", "Emotional nature · needs · instinct")}
{self.rising_entry()}
</section>

<section class="pb">
<h2><span class="no">Part Four</span>Planets in Sign &amp; House</h2>
{four}
</section>

<section class="pb">
<h2><span class="no">Part Five</span>Major Aspects</h2>
<p class="lead">Aspects are the angles between planets. Trines and sextiles flow, squares and
oppositions produce friction that builds strength, and conjunctions fuse two functions into
one. The orb is the distance from exact: the tighter, the louder.</p>
{asp}
<h3>Complete aspect list</h3>
{c["aspects_table"](d["aspects"])}
</section>

<section class="pb">
<h2><span class="no">Part Six</span>Synthesis</h2>
<p class="lead">If the chart were a single line: {lead}.</p>
{"".join(f"<p>{p}</p>" for p in synth)}
<p class="footer-note">Calculated with Swiss Ephemeris · Tropical zodiac · Placidus houses ·
Birth data as provided. Text assembled from rule tables, without a language model. Astrology
is offered here as a reflective language, not a deterministic science; take what is
useful.</p>
</section>
"""


def build(ctx, slug):
    return Chart(ctx, slug).build()
