"""Point Swiss Ephemeris at its real data files, and refuse to run without them.

pyswisseph ships no ephemeris data, and with none present it falls back to the
built-in Moshier analytical ephemeris silently: same API, same call, a return
flag nobody reads. The planets land under an arcsecond either way; the true node
does not, because Moshier's lunar theory is its weak spot.

Kerykeion adds a second problem: it hardcodes its own ephemeris directory
(astrological_subject_factory.py: ephe_path = <pkg>/sweph) and takes no
override. It bundles only seas_18.se1, the *asteroid* file, so the planet and
moon files are absent and every kerykeion chart has been running on Moshier.

So this module fetches the real files into <repo>/ephe and plants a copy in
kerykeion's own sweph directory, which is where it will actually look. That is
inside .venv and does not survive a reinstall, so the copy is re-checked on
every run rather than done once by hand.

    python pipeline/ephemeris.py --fetch
"""
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import swisseph as swe

REPO = Path(__file__).resolve().parent.parent

FILES = ("sepl_18.se1", "semo_18.se1")      # planets, moon; _18 covers 1800-2399
SOURCE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"
REPO_URL = "https://github.com/aloistr/swisseph"

_ready = False


def ephe_dir():
    return Path(os.environ.get("SE_EPHE_PATH") or (REPO / "ephe"))


def kerykeion_sweph():
    import kerykeion
    return Path(kerykeion.__file__).parent / "sweph"


def fetch_git(d, names):
    """Fallback for sandboxes that allow github.com but not raw.githubusercontent.com
    (the Claude Chat sandbox is one): a sparse, blob-filtered clone of the ephe files."""
    with tempfile.TemporaryDirectory() as tmp:
        def git(*a):
            subprocess.run(["git", *a], cwd=tmp, check=True, capture_output=True)
        git("clone", "--depth", "1", "--filter=blob:none", "--sparse", REPO_URL, "sw")
        tmp = str(Path(tmp) / "sw")
        git("sparse-checkout", "set", "--no-cone", *[f"ephe/{n}" for n in names])
        for n in names:
            shutil.copy2(Path(tmp) / "ephe" / n, d / n)


def fetch():
    d = ephe_dir()
    d.mkdir(parents=True, exist_ok=True)
    # EPHE_VIA_GIT=1 skips the raw download, to test the sandbox path.
    need = [] if os.environ.get("EPHE_VIA_GIT") else [f for f in FILES if not (d / f).exists()]
    for f in need:
        print(f"  fetching {f} ...", end="", flush=True)
        try:
            urllib.request.urlretrieve(f"{SOURCE}/{f}", d / f)
            print(f" {(d / f).stat().st_size:,} bytes")
        except OSError as e:
            (d / f).unlink(missing_ok=True)
            print(f" failed ({e.__class__.__name__}), will try git")
    rest = [f for f in FILES if not (d / f).exists()]
    if rest:
        print(f"  cloning {', '.join(rest)} from {REPO_URL} ...", flush=True)
        fetch_git(d, rest)
    return d


def init():
    """Make sure kerykeion will find real Swiss files, then prove it did.

    set_ephe_path succeeds whether or not the files exist, so the only honest
    check is to run a calculation and read which backend answered.
    """
    global _ready
    if _ready:
        return
    src = ephe_dir()
    if any(not (src / f).exists() for f in FILES):
        print("Swiss Ephemeris data files missing; fetching them (one time, ~1.8 MB).")
        try:
            fetch()
        except (OSError, subprocess.CalledProcessError) as e:
            print(f"  fetch failed: {e}")
    gone = [f for f in FILES if not (src / f).exists()]
    if gone:
        raise RuntimeError(
            f"Swiss Ephemeris data files missing from {src}: {', '.join(gone)}.\n"
            f"Without them swisseph falls back to Moshier and the node drifts.\n"
            f"Fetch them with:  python pipeline/ephemeris.py --fetch")

    # kerykeion looks in its own package dir and takes no override, so plant
    # them there. Cheap to re-check; .venv reinstalls wipe it.
    dst = kerykeion_sweph()
    dst.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        if not (dst / f).exists():
            shutil.copy2(src / f, dst / f)

    swe.set_ephe_path(str(dst))
    _, retflag = swe.calc_ut(swe.julday(2000, 1, 1, 12.0), swe.SUN, swe.FLG_SWIEPH)
    if not retflag & swe.FLG_SWIEPH:
        which = "Moshier" if retflag & swe.FLG_MOSEPH else f"unknown (flag {retflag})"
        raise RuntimeError(
            f"swisseph answered from the {which} ephemeris despite files in {dst}. "
            f"Refusing to run: the packet claims Swiss Ephemeris on its cover.")
    _ready = True


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        print(f"Swiss Ephemeris data -> {ephe_dir()}")
        fetch()
    init()
    print(f"OK: Swiss Ephemeris active, planted in {kerykeion_sweph()}")
