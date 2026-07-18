"""Skeleton for a natal content module. Copy to work/<dir>/content_<slug>.py and write.

Replace SLUG/NAME and every [TODO] with prose grounded in chart-data.json.
See content_guide.md for the section contract and writing rules.
"""


def big_three(ctx):
    """The Sun/Moon/Rising modules. Written once here; the synastry packet reuses them
    for its side-by-side opening section, so keep each entry self-contained."""
    return {
        "sun": """<div class="entry"><h3>[TODO: Sun in Sign] <span class="tag">[house · degree]</span></h3>
<div class="pos">Core identity · vitality · the life's purpose</div>
<p>[TODO: two paragraphs, sign then house]</p></div>""",
        "moon": """<div class="entry"><h3>[TODO: Moon in Sign] <span class="tag">[house · degree]</span></h3>
<div class="pos">Emotional nature · needs · instinct</div>
<p>[TODO]</p></div>""",
        "rising": """<div class="entry"><h3>[TODO: Rising sign] <span class="tag">Ascendant [degree]</span></h3>
<div class="pos">The outward self · first impressions · the body's style</div>
<p>[TODO]</p></div>""",
    }


def build(ctx):
    d = ctx["data"]["subjects"]["SLUG"]
    pos_tbl = ctx["positions_table"](d)
    hse_tbl = ctx["houses_table"](d)
    elem_tbl, mode_tbl = ctx["balance_tables"](d)
    asp_tbl = ctx["aspects_table"](d["aspects"])
    wheel = ctx["svg_inline"](ctx["workdir"] / "wheel-SLUG.svg")
    b3 = big_three(ctx)

    return f"""
<div class="cover">
  <div class="kicker">Natal Chart · Tropical Zodiac · Placidus Houses · Swiss Ephemeris</div>
  <h1>NAME</h1>
  <div class="birthdata">[TODO: date · time zone · city · coordinates]</div>
  <hr class="rule">
  <div class="bigthree">
    <div><div class="lbl">Sun</div><div class="val">[TODO]</div></div>
    <div><div class="lbl">Moon</div><div class="val">[TODO]</div></div>
    <div><div class="lbl">Rising</div><div class="val">[TODO]</div></div>
  </div>
  <div class="wheelwrap">{wheel}</div>
  <div class="foot">[TODO: lunar phase · day/night birth]</div>
</div>

<section class="pb">
<h2><span class="no">Part One</span>The Chart at a Glance</h2>
<p class="lead">Every symbol in this packet was calculated with the Swiss Ephemeris, the same
planetary engine used by professional astrology software, for the exact minute and coordinates
of birth. Positions use the tropical zodiac and Placidus houses, the standard in modern Western
practice.</p>
<div class="callout"><div class="ttl">Three signatures to hold onto</div>
<p><b>1. [TODO].</b> [TODO]</p>
<p><b>2. [TODO].</b> [TODO]</p>
<p><b>3. [TODO].</b> [TODO]</p></div>
<div class="cols2"><div>{elem_tbl}</div><div>{mode_tbl}</div></div>
<p class="footer-note">Tallies count the ten planets (Sun through Pluto). [TODO: one line on
what the balance means.]</p>
<h3>[TODO: sect + lunar phase heading]</h3>
<p>[TODO]</p>
<h3>The chart ruler</h3>
<p>[TODO]</p>
</section>

<section class="pb">
<h2><span class="no">Part Two</span>Positions &amp; Houses</h2>
<h3>Planetary positions</h3>
{pos_tbl}
<div class="cols2">
<div><h3>House cusps (Placidus)</h3>{hse_tbl}</div>
<div><h3>Reading the table</h3>
<p>℞ marks a planet that was retrograde, appearing to move backward from Earth's point of
view. Retrograde planets tend to work internally first: their themes are processed privately
before they are expressed.</p>
<p>Houses are the twelve arenas of life, counted from the Ascendant. Where a planet falls by
house tells you <i>where</i> its energy plays out; the sign tells you <i>how</i>.</p>
<p>The angles (Ascendant, Midheaven, Descendant, IC) are the chart's compass points: self,
public direction, partnership, and roots.</p></div>
</div>
</section>

<section class="pb">
<h2><span class="no">Part Three</span>The Big Three</h2>

{b3["sun"]}

{b3["moon"]}

{b3["rising"]}
</section>

<section class="pb">
<h2><span class="no">Part Four</span>Planets in Sign &amp; House</h2>
<!-- One .entry per point: Mercury, Venus, Mars, Jupiter, Saturn, Uranus, Neptune,
     Pluto, Chiron, North Node, Lilith, Midheaven -->
<div class="entry"><h3>[TODO] <span class="tag">[house · degree]</span></h3>
<p>[TODO]</p></div>
</section>

<section class="pb">
<h2><span class="no">Part Five</span>Major Aspects</h2>
<p class="lead">Aspects are the geometric conversations between planets. Trines and sextiles
flow; squares and oppositions produce friction that builds strength; conjunctions fuse two
voices into one. Orb is the distance from exactness: the tighter, the louder.</p>
<!-- ~10-12 of the tightest / most personal aspects -->
<div class="aspect-entry"><div class="asp-line">[glyph] [Point] <span class="g">[aspect
glyph]</span> [Point] [glyph] <span class="orb">[aspect · orb]</span></div>
<p>[TODO]</p></div>
<h3>Complete aspect list</h3>
{asp_tbl}
</section>

<section class="pb">
<h2><span class="no">Part Six</span>Synthesis</h2>
<p class="lead">If the chart were a single sentence: [TODO].</p>
<p>[TODO: 3-4 paragraphs]</p>
<p class="footer-note">Calculated with Swiss Ephemeris · Tropical zodiac · Placidus houses ·
Birth data as provided. Astrology is offered here as a reflective language, not a
deterministic science; take what is useful.</p>
</section>
"""
