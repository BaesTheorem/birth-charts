# Writing content modules

The pipeline computes everything mechanical (positions, houses, aspects, overlays, wheels,
score). The prose is yours. Each work dir needs one `content_<slug>.py` per subject and,
if a pair is declared, `content_synastry.py`. Each module exposes `build(ctx) -> str`
returning the packet's body HTML. Start from `content_template.py`.

## The ctx dict

| key | what it gives you |
|---|---|
| `data` | full chart-data.json: `data["subjects"][slug]` (points, houses, aspects, lunar_phase, local time), `data["synastry"]` (aspects, pair, score), `data["config"][slug]` (birth data as entered) |
| `positions_table(subj)` | rendered positions table |
| `houses_table(subj)` | Placidus cusp table |
| `balance_tables(subj)` | (element_table, modality_table) over the ten planets |
| `aspects_table(aspects, dual=, names=)` | full aspect list table |
| `overlay_table(owner, partner, owner_name, partner_name)` | synastry house overlays |
| `score_table(data["synastry"]["score"])` | Discepolo scorecard table: one row per scored item plus the total |
| `svg_inline(path)` | inline an SVG; wheels live at `workdir / "wheel-<slug>.svg"`, `synastry-wheel.svg`, `synastry-grid.svg` |
| `fmt_deg(pos)` | 7.67 → `7°40′` |
| `workdir` | Path to the work dir |

## Natal packet structure (keep this order)

1. **Cover** — kicker, name, birth line, big three, wheel, lunar phase + sect footer
2. **Part One: The chart at a glance** — method note, a "three signatures" callout (the
   3 most load-bearing patterns in THIS chart), balance tables, sect + lunar phase
   paragraph, chart ruler paragraph
3. **Part Two: Positions & houses** — tables plus a short "reading the table" explainer
4. **Part Three: The big three** — Sun, Moon, Ascendant in depth (sign AND house)
5. **Part Four: Planets in sign & house** — Mercury through Pluto, Chiron, North Node,
   Lilith, Midheaven
6. **Part Five: Major aspects** — the ~10-12 tightest/most personal, then the full table
7. **Part Six: Synthesis** — one-sentence lead, then 3-4 paragraphs weaving the themes,
   plus the methods footer

**Natal packets stand alone.** Never reference the synastry packet, the other person, or
the relationship from inside a natal packet: each one must read as a complete, private
document its subject could receive by itself. Cross-chart observations belong only in the
synastry packet.

## Synastry packet structure (optional add-on)

Only produce this when a pair is declared in `subjects.yaml` and the user asked for it.
The natal packets are the primary deliverable; synastry is an add-on that builds on them.

1. Cover (bi-wheel, both birth lines, three headline stats)
2. How to read this chart + elemental comparison callout
3. The Discepolo scorecard: a dedicated section with `score_table(...)` showing each
   scored item and its points, the band table (0-5 minimal / 5-10 medium / 10-15
   important / 15-20 very important / 20-30 exceptional / 30+ rare exceptional), a note
   on which chart owns which point in each row, and an honest reading (what scored,
   what the method ignores). Explain the checklist: Sun-Sun, Sun-Moon, Sun/Moon to
   Ascendant, Venus-Mars, destiny-sign bonus; 8 vs 11 points at ≤2° orb, 4 for the rest.
4. The headline aspects (Sun-Moon contacts first, always: they are what astrologers
   check first)
5. Channel by channel: minds, love, drive, growth, commitment, depth/healing, nodes
6. House overlays: both tables + "what stands out" bullets
7. The honest ledger: what flows / what takes work, side by side
8. Synthesis + methods footer
9. Appendix: aspect grid SVG + complete aspect table

## Writing rules (non-negotiable)

- **Ground every claim in the computed data.** Name the placement, the house, the orb.
  Never write a sentence that could sit in anyone's chart.
- **Plain language.** Every technical term gets translated in the same breath the first
  time it appears ("its own sign, its strongest placement, called domicile").
- **Honest, not fatalistic.** Hard aspects get real names and a workable framing. No doom,
  no flattery. Every chart gets a "what takes work" treatment somewhere.
- **The de-AI pass is part of the build, not optional.** After drafting, run the `/de-ai`
  checklist over the prose. Specifically hunt:
  - em dashes (banned outright, use commas/periods/parentheses/colons)
  - metaphorical "quietly" + hype adverbs (effortlessly, seamlessly, simply)
  - the correctio pattern ("It is not X; it is Y") — one per packet at most
  - "genuinely / precisely / truly / remarkable / profound" — grep and thin them out
  - repeated openers ("This is a person who…", "This is the signature of…")
  - three-item lists stacked in consecutive sentences
  - identical stock sentences copied between the two natal packets (shared boilerplate
    like the method note is fine; interpretive sentences are not)
- Attribute the method honestly (Swiss Ephemeris, Placidus, tropical) and keep the
  closing disclaimer: astrology as reflective language, not deterministic science.

## Astrological conventions used

- Sect: births with the Sun below the horizon are night charts; say so and weight the
  Moon accordingly.
- Note domicile/exaltation when a planet has it; note the traditional house "joys"
  (Saturn 12th, Jupiter 11th, Mars 6th, Sun 9th, Moon 3rd, Venus 5th, Mercury 1st).
- Stelliums: 3+ planets in one sign or house get called out as a chart signature.
- Missing elements are as load-bearing as concentrations; check the balance tables.
- In synastry, lead with luminaries, then Venus/Saturn (durability), Jupiter/Nodes
  (growth), Mars/Pluto (friction), angles and overlays. Double-check which chart is p1:
  in `data["synastry"]["aspects"]`, p1 belongs to the first slug in the pair.
