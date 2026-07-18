# birth-charts

Printable natal-chart PDF packets, computed with the Swiss Ephemeris and typeset for
paper. One YAML file of birth data in, one Letter-size natal packet out per person, with
chart wheels, full position/house/aspect tables, and room for plain-language
interpretation. Declaring a pair adds an optional synastry packet (bi-wheel, interaspects,
house overlays) on top. Natal packets are self-contained and never reference the synastry
material.

The mechanical layer is fully automated (ephemeris math, wheel SVGs, every table, PDF
layout). The interpretive prose is deliberately not: each packet's readings are written
per person into small Python content modules, following the contract in
[`pipeline/content_guide.md`](pipeline/content_guide.md).

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

## Use

```bash
mkdir -p work/my-charts
cp subjects.example.yaml work/my-charts/subjects.yaml   # edit with real birth data
.venv/bin/python make.py work/my-charts
```

The first run stops after the compute step and lists the content modules the work dir
still needs. Write them (start from `pipeline/content_template.py`, follow
`pipeline/content_guide.md`), then run `make.py` again. PDFs land in `work/my-charts/out/`,
or pass `--dest ~/somewhere` to drop them elsewhere.

`work/` is gitignored on purpose: real people's birth data and readings stay local.

## Method

Tropical zodiac, Placidus houses, true node, mean Lilith. Natal aspect orbs follow
Kerykeion's defaults. Synastry packets include the Discepolo relationship score for
color; the guide treats it as one yardstick, not a verdict.
