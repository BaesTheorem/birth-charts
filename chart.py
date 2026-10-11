"""One command from birth data to a finished natal packet.

    python chart.py "Ada" 1990-04-12 14:30 "Kansas City, MO"
    python chart.py "Ada" 1990-04-12 unknown "Lagos, Nigeria"
    python chart.py "Ada" 1990-04-12 14:30 "Somewhere" --lat 39.1 --lng -94.6 --tz America/Chicago
    python chart.py "Ada" 1990-04-12 14:30 "Kansas City, MO" --with "Sam" 1988-11-02 07:15 "Omaha, NE"

--with adds a second person: you get both natal packets and a synastry packet.

Finds the birthplace in an offline city list (GeoNames, towns of 1,000+ people),
writes work/<slug>/subjects.yaml, and runs make.py --auto. The packet lands in
work/<slug>/out/ (or --dest). To replace the rule-table synthesis with written
prose, follow the steps it prints at the end.
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent


def slugify(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "chart"


def geocode(place):
    import geonamescache

    gc = geonamescache.GeonamesCache(min_city_population=1000)
    states = {c: s["name"].lower() for c, s in gc.get_us_states().items()}
    countries = {c: v["name"].lower() for c, v in gc.get_countries().items()}
    parts = [p.strip() for p in place.split(",") if p.strip()]
    city, quals = parts[0].lower(), [q.lower() for q in parts[1:]]

    def fits(c, q):
        cc = c["countrycode"]
        return (q.upper() == cc or q == countries.get(cc)
                or (q in ("usa", "us", "united states", "america") and cc == "US")
                or (cc == "US" and (q.upper() == c["admin1code"]
                                    or q == states.get(c["admin1code"]))))

    hits = [c for c in gc.get_cities().values()
            if (c["name"].lower() == city
                or city in (a.lower() for a in c.get("alternatenames", [])))
            and all(fits(c, q) for q in quals)]
    hits.sort(key=lambda c: -c["population"])
    return hits


def person(name, date, time, place, lat=None, lng=None, tz=None, slug=None):
    y, mo, d = (int(x) for x in date.split("-"))
    unknown = time.lower() == "unknown"
    h, mi = (12, 0) if unknown else (int(x) for x in time.split(":"))
    if None not in (lat, lng, tz):
        nation = "US"
    else:
        hits = geocode(place)
        if not hits:
            sys.exit(f'Could not find "{place}". Add the state or country, or pass '
                     "--lat, --lng and --tz.")
        top = hits[0]
        lat, lng, tz, nation = (top["latitude"], top["longitude"], top["timezone"],
                                top["countrycode"])
        print(f"{name}'s birthplace: {top['name']}, {top['admin1code']}, {nation} "
              f"({lat:.4f}, {lng:.4f}, {tz})")
        if len(hits) > 1:
            other = "; ".join(f"{c['name']}, {c['admin1code']}, {c['countrycode']}"
                              for c in hits[1:4])
            print(f"  Other matches: {other}. If this is wrong, add the state or "
                  "country to the place.")
    subj = {"slug": slug or slugify(name), "name": name, "year": y, "month": mo, "day": d,
            "hour": h, "minute": mi, "city": place.split(",")[0].strip(),
            "nation": nation, "lat": lat, "lng": lng, "tz": tz}
    if unknown:
        subj["time_unknown"] = True
        print(f"WARNING: {name}'s birth time is unknown. The chart uses noon, so the Moon "
              "can be off by up to about 7 degrees, and the Ascendant, Midheaven and "
              "houses are placeholders.")
    return subj


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name")
    ap.add_argument("date", help="YYYY-MM-DD")
    ap.add_argument("time", help="HH:MM, 24-hour local time, or 'unknown'")
    ap.add_argument("place", help='"City, State" or "City, Country"')
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    ap.add_argument("--tz", help="IANA time zone, for example America/Chicago")
    ap.add_argument("--slug")
    ap.add_argument("--dest", help="folder for the finished packet")
    ap.add_argument("--with", dest="partner", nargs=4, metavar=("NAME", "DATE", "TIME", "PLACE"),
                    help="a second person, for a synastry packet")
    a = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    people = [person(a.name, a.date, a.time, a.place, a.lat, a.lng, a.tz, a.slug)]
    if a.partner:
        people.append(person(*a.partner))
    slug = "-".join(p["slug"] for p in people)
    workdir = REPO / "work" / slug
    workdir.mkdir(parents=True, exist_ok=True)
    doc = {"subjects": people}
    if len(people) == 2:
        doc["synastry"] = [p["slug"] for p in people]
    (workdir / "subjects.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))

    cmd = [sys.executable, str(REPO / "make.py"), str(workdir), "--auto"]
    if a.dest:
        cmd += ["--dest", a.dest]
    subprocess.run(cmd, check=True)

    rel = workdir.relative_to(REPO)
    print(f"""
Done: rule-table packet in {a.dest or rel / 'out'}.

Optional written layer (signatures + synthesis, checked against the chart):
  1. python pipeline/prose.py brief {rel} <who>     # read the brief
  2. write {rel}/prose_<who>.json in the shape it shows
  3. python pipeline/prose.py check {rel} <who>
  4. python make.py {rel} --auto{' --dest ' + a.dest if a.dest else ''}
  where <who> is one of: {', '.join([p['slug'] for p in people] + (['synastry'] if len(people) == 2 else []))}""")


if __name__ == "__main__":
    main()
