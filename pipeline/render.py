"""Render built HTML packets to Letter PDFs via Playwright (true headless, no screen flash).

Usage: python pipeline/render.py work/<dir> [dest_dir]
Default dest: work/<dir>/out. PDFs are named from the subjects' display names.

If no browser can start (Playwright missing, or its Chromium download blocked, as
in the Claude Chat sandbox), the self-contained HTML packets are copied to dest
instead. They open in any browser and print to PDF from there (Letter size).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:  # noqa: BLE001 -- any launch failure means "no browser yet"
        print("Chromium for Playwright is missing; installing it (one time) ...")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"],
                       check=False, timeout=600)
        return p.chromium.launch()


def html_fallback(jobs, why):
    print(f"No PDF renderer ({why}). Copying the HTML packets instead; open one in a "
          "browser and print it to PDF (Letter, background graphics on).")
    for html, pdf in jobs:
        out = pdf.with_suffix(".html")
        if out.resolve() != html.resolve():
            shutil.copy2(html, out)
        print("wrote", out)


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

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return html_fallback(jobs, "playwright is not installed")
    with sync_playwright() as p:
        try:
            b = launch(p)
        except Exception as e:  # noqa: BLE001 -- report and fall back to HTML
            return html_fallback(jobs, f"{e.__class__.__name__}: {str(e).splitlines()[0]}")
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
