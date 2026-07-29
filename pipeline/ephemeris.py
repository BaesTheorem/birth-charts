"""Point Swiss Ephemeris at its real data files, and refuse to run without them.

Same problem as the Human Design pipeline's ephemeris.py, one extra wrinkle.
pyswisseph ships no ephemeris data, and with none present it falls back to the
built-in Moshier analytical ephemeris silently: same API, same call, a return
flag nobody reads. The planets land under an arcsecond either way; the true node
does not, because Moshier's lunar theory is its weak spot.

The wrinkle: kerykeion hardcodes its own ephemeris directory
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
import sys
import urllib.request
from pathlib import Path

import swisseph as swe

REPO = Path(__file__).resolve().parent.parent

FILES = ("sepl_18.se1", "semo_18.se1")      # planets, moon; _18 covers 1800-2399
SOURCE = "https://raw.githubusercontent.com/aloistr/swisseph/master/ephe"

_ready = False


def ephe_dir():
    return Path(os.environ.get("SE_EPHE_PATH") or (REPO / "ephe"))


def kerykeion_sweph():
    import kerykeion
    return Path(kerykeion.__file__).parent / "sweph"


def fetch():
    d = ephe_dir()
    d.mkdir(parents=True, exist_ok=True)
    for f in FILES:
        dest = d / f
        if dest.exists():
            print(f"  have {f}")
            continue
        print(f"  fetching {f} ...", end="", flush=True)
        urllib.request.urlretrieve(f"{SOURCE}/{f}", dest)
        print(f" {dest.stat().st_size:,} bytes")
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
