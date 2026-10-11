# Instructions for AI assistants

Someone gave you this repo and asked for a birth chart. This file is the whole procedure.
It works in a sandbox that can reach only GitHub and PyPI (Claude Chat's code execution
is one).

## 1. Get the birth data

You need four things for each person: a name or label, the birth date, the local birth
time, and the birthplace (city plus state or country). If the time is not known, use
`unknown` and tell the user that the Ascendant, Midheaven and houses are then
placeholders. Do not ask for coordinates.

## 2. Install

```bash
git clone --depth 1 https://github.com/BaesTheorem/birth-charts
cd birth-charts
pip install -r requirements.txt
```

On Python 3.12 or later, `pyswisseph` builds from source, which needs a C compiler and
takes a minute. Do not try to install a browser by hand: `render.py` does that, and falls
back to HTML when it cannot.

## 3. Compute and build the rule-table packet

```bash
python chart.py "Ada" 1990-04-12 14:30 "Kansas City, MO"
```

Read the `Birthplace:` line it prints. If it chose the wrong town, run it again with the
state or country in the place, or with `--lat --lng --tz`. The packet is now complete,
written from rule tables without a language model.

## 4. Write the signatures and synthesis (recommended)

This is the step where you add value. The rule tables list placements; you connect them.

```bash
python pipeline/prose.py brief work/ada ada
```

Read the brief, then write `work/ada/prose_ada.json` in the shape it shows: three
signatures, a one-line lead, and three or four synthesis paragraphs. Follow the rules in
the brief and in [`pipeline/content_guide.md`](pipeline/content_guide.md) ("Writing
rules"). In short: every claim names a real placement, house or orb from the brief; plain
language; honest about hard aspects; no em dashes, no hype adverbs; no pronouns you were
not given.

```bash
python pipeline/prose.py check work/ada ada    # fix every UNGROUNDED line it prints
python make.py work/ada --auto
```

The build refuses prose that fails the check. Do not work around the check: if it flags
a sentence, the sentence is wrong, or it says something the brief does not support.

## 5. Deliver

The packet is `work/ada/out/Ada - Natal Chart.pdf`, or `.html` if no PDF renderer could
start. Give the user that file (copy it to your outputs folder if your environment has
one). Tell them the big three (Sun, Moon, Rising) and the three signatures in a few
lines. If you delivered HTML, tell them to open it in a browser and print to PDF with
background graphics on.

## Two people (synastry)

Only when the user asks for a relationship or compatibility reading:

```bash
python chart.py "Ada" 1990-04-12 14:30 "Kansas City, MO" --with "Sam" 1988-11-02 07:15 "Omaha, NE"
```

You get both natal packets and `Ada & Sam - Synastry` in `work/ada-sam/out/`. For the
written layer, do step 4 for each person, then `brief`/`check` with `synastry` as the
slug and save `work/ada-sam/prose_synastry.json`. In the synastry prose, name both owners
in every contact ("Ada's Venus trines Sam's Mars"): the checker reads that form, and it
rejects a contact with the owners swapped. Add the optional `attraction` key only if the
user asked for that section.

## Privacy

Birth data is personal. Everything under `work/` is gitignored. Never commit it, and do
not paste the birth data anywhere other than the chat.
