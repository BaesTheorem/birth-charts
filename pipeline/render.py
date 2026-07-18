"""Render built HTML packets to Letter PDFs via Playwright (true headless, no screen flash).

Usage: python pipeline/render.py work/<dir> [dest_dir]
Default dest: work/<dir>/out. PDFs are named from the subjects' display names.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    workdir = Path(sys.argv[1]).resolve()
    dest = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else workdir / "out"
    dest.mkdir(parents=True, exist_ok=True)
    data = json.loads((workdir / "chart-data.json").read_text())
    outdir = workdir / "out"

    jobs = []
    for slug, subj in data["subjects"].items():
        if (outdir / f"{slug}.html").exists():
            jobs.append((outdir / f"{slug}.html", dest / f"{subj['name']} - Natal Chart.pdf"))
    if (outdir / "synastry.html").exists():
        names = [data["subjects"][s]["name"] for s in data["synastry"]["pair"]]
        jobs.append((outdir / "synastry.html", dest / f"{names[0]} & {names[1]} - Synastry.pdf"))

    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        for html, pdf in jobs:
            pg.goto(f"file://{html}", wait_until="networkidle")
            pg.pdf(path=str(pdf), format="Letter", print_background=True,
                   margin={"top": "0.6in", "bottom": "0.6in",
                           "left": "0.7in", "right": "0.7in"})
            print("wrote", pdf)
        b.close()


if __name__ == "__main__":
    main()
