#!/usr/bin/env python3
"""
zac-is-back, step 2: isolate the burned-in pink verse from each supplied spread
as a transparent PNG, ready to composite back onto the animated clip.

    images-text/page-NN-slug.png
        --(colour key on the lettering pink)-->
    overlays/page-NN-slug.png        (1920x1080, lettering only, rest transparent)

Same contain-fit as the clean plates, so the overlay drops onto its clip at
overlay=0:0 in step 3. Pure Pillow -- no API, no cost, no video.

The key is a per-channel box around the lettering colour (~ #C45585) plus a
"more blue than green" test to reject Zac's coral nose / lips / skin. On the
~9 spreads where the verse sits on clean white it is essentially exact; on the
pages flagged NEEDS_TOUCHUP the verse overlaps artwork or a bubble, so treat the
output as a starting point and tidy it in an image editor.

Usage:
    python build_overlays.py                    # every page missing an overlay
    python build_overlays.py --page 08 --force
    python build_overlays.py --contact-sheet    # write overlays/_check.png to review all keys
"""
import argparse
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

from zac_lib import OVERLAYS, fit_16x9_rgba, page_id, text_plates

INK = (196, 84, 133)   # hand-lettering colour, sampled across spreads
TOL = 46               # per-channel tolerance box around INK
BLUE_OVER_GREEN = 34   # lettering has b-g ~49; Zac's lips / open mouth do not
FEATHER = 0.6          # px gaussian blur on the alpha edge

# Verse overlaps artwork or a speech bubble here -- auto key needs a hand pass.
NEEDS_TOUCHUP = {"02", "03", "06", "08", "12", "15", "16"}


def band_box(band: Image.Image, centre: int, tol: int) -> Image.Image:
    lo, hi = centre - tol, centre + tol
    return band.point(lambda v: 255 if lo <= v <= hi else 0)


def key_lettering(src: Path) -> Image.Image:
    rgb = Image.open(src).convert("RGB")
    r, g, b = rgb.split()

    mask = band_box(r, INK[0], TOL)
    mask = ImageChops.multiply(mask, band_box(g, INK[1], TOL))
    mask = ImageChops.multiply(mask, band_box(b, INK[2], TOL))
    bluer = ImageChops.subtract(b, g).point(lambda v: 255 if v >= BLUE_OVER_GREEN else 0)
    mask = ImageChops.multiply(mask, bluer)

    if FEATHER:
        mask = mask.filter(ImageFilter.GaussianBlur(FEATHER))

    out = Image.new("RGBA", rgb.size, (0, 0, 0, 0))
    out.paste(rgb.convert("RGBA"), (0, 0), mask)
    return fit_16x9_rgba(out)


def contact_sheet(paths: list[Path]) -> None:
    cols, thumb = 4, (480, 270)
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * thumb[0], rows * thumb[1]), (110, 110, 110))
    for i, p in enumerate(paths):
        cell = Image.new("RGB", thumb, (110, 110, 110))
        t = Image.open(p).convert("RGBA").resize(thumb)
        cell.paste(t, (0, 0), t)
        sheet.paste(cell, ((i % cols) * thumb[0], (i // cols) * thumb[1]))
    sheet.save(OVERLAYS / "_check.png")
    print(f"  wrote {(OVERLAYS / '_check.png')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", metavar="NN")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--contact-sheet", action="store_true")
    args = ap.parse_args()

    OVERLAYS.mkdir(exist_ok=True)
    plates = text_plates()
    if args.page:
        pid = args.page.zfill(2)
        plates = [p for p in plates if page_id(p) == pid]

    produced: list[Path] = []
    for src in plates:
        dest = OVERLAYS / f"{src.stem}.png"
        if dest.exists() and not args.force:
            print(f"  [{src.stem}] overlay exists -- skipping")
        else:
            key_lettering(src).save(dest)
            flag = "   <- touch up by hand" if page_id(src) in NEEDS_TOUCHUP else ""
            print(f"  [{src.stem}] -> {dest.name}{flag}")
        produced.append(dest)

    if args.contact_sheet:
        contact_sheet(sorted(produced))
    print("\nDone.")


if __name__ == "__main__":
    main()
