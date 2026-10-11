# birth-charts

Printable natal-chart PDF packets, computed with the Swiss Ephemeris and typeset for
paper. One YAML file of birth data in, one Letter-size natal packet out per person, with
chart wheels, full position/house/aspect tables, and room for plain-language
interpretation. Declaring a pair adds an optional synastry packet (bi-wheel, interaspects,
house overlays) on top. Natal packets are self-contained and never reference the synastry
material.

## Quickest start: ask Claude

Paste this into a Claude chat (with code execution on), with your own details:

> Make me a natal chart packet with https://github.com/BaesTheorem/birth-charts.
> Name: Ada. Born 1990-04-12 at 2:30 PM in Kansas City, MO.

Claude clones the repo, follows [`AGENTS.md`](AGENTS.md), and gives back the packet. If
you do not know the birth time, say so: you get a chart drawn for noon, with the
time-sensitive parts marked.

## How it works

Three layers, each one optional on top of the last:

1. **Computed:** ephemeris math, wheel SVGs, every table, PDF layout.
2. **Rule tables (`--auto`):** a complete reading assembled from keyword tables for each
   planet, sign, house and aspect, led by the chart's ranked signatures
   (`pipeline/facts.py`, `pipeline/delineate.py`). No language model is involved.
3. **Written:** the signatures and the synthesis rewritten from a brief
   (`pipeline/prose.py brief`), then checked against the chart (`prose.py check`) so a
   wrong placement cannot reach the page. Or write the whole packet by hand as a content
   module, following [`pipeline/content_guide.md`](pipeline/content_guide.md).

## Stack

- [Kerykeion](https://github.com/g-battaglia/kerykeion) on pyswisseph (Swiss Ephemeris)
  for positions, Placidus houses, aspects, synastry, and wheel SVGs
- A custom print theme (`theme/elegant.css`) swapped into the generated SVGs: ink navy,
  antique gold, ivory paper
- HTML + print CSS (`pipeline/style.css`), rendered to PDF by headless Chromium via
  Playwright

## Setup

```bash
uv venv .venv
uv pip install --python .venv/bin/python -r requirements.txt
.venv/bin/playwright install chromium   # if not already present
```

Plain `pip` works too, inside a venv (`python3 -m venv .venv`, then
`pip install -U pip setuptools wheel` before the requirements). The Swiss Ephemeris data files
(~1.8 MB) download on the first run. For PDFs the renderer uses Playwright's own
Chromium, or any other Chromium already installed, or downloads one. If all of those fail,
you get the HTML packet to print from a browser.

## Use

One person, one command:

```bash
.venv/bin/python chart.py "Ada" 1990-04-12 14:30 "Kansas City, MO"
```

The place is found in an offline city list; pass `--lat --lng --tz` to skip that.
Pass `unknown` as the time if it is not known.

Add `--with NAME DATE TIME PLACE` for a second person: you get both natal packets and a
synastry packet, all from rule tables.

For hand-written packets, use a YAML file:

```bash
mkdir -p work/my-charts
cp subjects.example.yaml work/my-charts/subjects.yaml   # edit with real birth data
.venv/bin/python make.py work/my-charts
```

The first run stops after the compute step and lists the content modules the work dir
still needs. Write them (start from `pipeline/content_template.py`, follow
`pipeline/content_guide.md`), then run `make.py` again. PDFs land in `work/my-charts/out/`,
or pass `--dest ~/somewhere` to drop them elsewhere.

To skip the writing step, pass `--auto`. Each natal packet without a content module is
then written from rule tables (`pipeline/delineate.py`): keyword phrases for each planet,
sign, house and aspect, plus the ranked signatures from `pipeline/facts.py` (natal) or the
ranked contacts from `pipeline/synastry.py` (pairs). No language model is involved, so
every sentence traces back to a placement or an orb. The prose is plainer and more
repetitive than a written module.

`.venv/bin/python pipeline/facts.py work/my-charts` prints the ranked signatures alone,
which is a good starting outline for a written module.

`work/` is gitignored on purpose: real people's birth data and readings stay local.

## Method

Tropical zodiac, Placidus houses, true node, mean Lilith. Natal aspect orbs follow
Kerykeion's defaults. Synastry packets include the Discepolo relationship score for
color; the guide treats it as one yardstick, not a verdict.

## License

Copyright (C) 2026 Alex Hedtke. Released under the GNU Affero General Public License
v3.0; see [`LICENSE`](LICENSE). The AGPL matches the license of
[Kerykeion](https://github.com/g-battaglia/kerykeion), which this project builds on.
The Swiss Ephemeris data files are not part of this repo: `pipeline/ephemeris.py`
downloads them from [Astrodienst's repository](https://github.com/aloistr/swisseph),
under Astrodienst's own terms (AGPL or their professional license).
