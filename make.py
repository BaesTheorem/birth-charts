"""One-command pipeline: compute ephemeris data + wheels, build HTML, render PDFs.

    .venv/bin/python make.py work/<dir> [--dest <pdf output dir>]

Stops after compute if the work dir has no content modules yet, and prints what
still needs to be written (see pipeline/content_guide.md).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent
PY = sys.executable


def run(script, *args):
    subprocess.run([PY, str(REPO / "pipeline" / script), *args], check=True)


def main():
    args = sys.argv[1:]
    dest = []
    if "--dest" in args:
        i = args.index("--dest")
        dest = [args[i + 1]]
        args = args[:i] + args[i + 2:]
    workdir = Path(args[0]).resolve()

    run("compute.py", str(workdir))

    data = json.loads((workdir / "chart-data.json").read_text())
    missing = [f"content_{slug}.py" for slug in data["subjects"]
               if not (workdir / f"content_{slug}.py").exists()]
    if "synastry" in data and not (workdir / "content_synastry.py").exists():
        missing.append("content_synastry.py")
    if missing:
        print("\nCompute done. Still needed before build (see pipeline/content_guide.md):")
        for m in missing:
            print("  -", workdir / m)
        sys.exit(2)

    run("build.py", str(workdir))
    run("render.py", str(workdir), *dest)


if __name__ == "__main__":
    main()
