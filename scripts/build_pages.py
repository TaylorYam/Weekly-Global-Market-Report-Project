"""Assemble only the three approved portfolio pages from canonical sources."""

from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PAGES = {
    "index.html": "pages/index.html",
    "historical/20260914/index.html": "examples/historical/20260914.html",
    "synthetic/index.html": "examples/sample_output.html",
}


def main():
    existing = {p.relative_to(SITE).as_posix() for p in SITE.rglob("*") if p.is_file()}
    if existing - PAGES.keys():
        raise ValueError("Site directory contains files outside the approved three-page manifest")
    for target, source in PAGES.items():
        destination = SITE / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        copyfile(ROOT / source, destination)
        if destination.read_bytes() != (ROOT / source).read_bytes():
            raise ValueError("Assembled page differs from its canonical source")
    print("Assembled landing page, one historical report and one synthetic demo.")


if __name__ == "__main__":
    main()
