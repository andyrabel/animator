#!/usr/bin/env python3
"""
zac-is-back, step 1: strip the burned-in verse from each supplied spread and
write a clean 16:9 plate for animate.py to feed to Kling.

    images-text/page-NN-slug.png
        --(FLUX Kontext text removal)-->
    images/page-NN-slug.jpg          (1920x1080, letterboxed on white)

Every spread has hand-lettered pink verse; pages 08 / 12 / 16 also have a
speech bubble that only holds text. Kontext removes them. The result is forced
back onto the original canvas and contain-fitted to exactly 1920x1080 so Kling
gets a true 16:9 frame and the overlays line up in step 3.

Costs ~$0.04 per page on fal.ai (~$0.64 for the book). Does NOT generate video.

Usage:
    python build_clean.py                 # every page missing a clean plate
    python build_clean.py --page 08       # one page
    python build_clean.py --force         # redo even if images/ plate exists
"""
import argparse
import base64
import os
import sys
import time
import urllib.request
from io import BytesIO
from pathlib import Path

import fal_client
from dotenv import load_dotenv
from PIL import Image

from zac_lib import IMAGES, fit_16x9, page_id, text_plates

KONTEXT_ENDPOINT = "fal-ai/flux-pro/kontext"
PROMPT = (
    "Remove all the pink handwritten text and words from this children's book "
    "illustration, and remove any speech-bubble shape that only contains text. "
    "Keep every character, object, colour, drawn line and the plain white "
    "background exactly as they are. Do not add, move, restyle or redraw "
    "anything else."
)
API_MAX_WIDTH = 1920       # downscale before upload; Kontext returns ~this width
BUBBLE_PAGES = {"08", "12", "16"}
RETRIES = 3
RETRY_WAIT = 5


def data_url(img: Image.Image) -> str:
    buf = BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=95)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def run_with_retry(label: str, fn):
    for attempt in range(1, RETRIES + 1):
        try:
            return fn()
        except Exception as exc:  # noqa: BLE001 - report and retry
            if attempt == RETRIES:
                raise
            print(f"  [{label}] {exc} -- retry {attempt}/{RETRIES}")
            time.sleep(RETRY_WAIT)


def clean_page(src: Path, force: bool) -> None:
    dest = IMAGES / f"{src.stem}.jpg"
    if dest.exists() and not force:
        print(f"  [{src.stem}] clean plate exists -- skipping")
        return

    original = Image.open(src)
    upload = original.copy()
    if upload.width > API_MAX_WIDTH:
        h = round(upload.height * API_MAX_WIDTH / upload.width)
        upload = upload.resize((API_MAX_WIDTH, h), Image.LANCZOS)

    print(f"  [{src.stem}] Kontext text removal ...", flush=True)
    result = run_with_retry(
        src.stem,
        lambda: fal_client.run(
            KONTEXT_ENDPOINT,
            arguments={
                "image_url": data_url(upload),
                "prompt": PROMPT,
                "output_format": "jpeg",
            },
        ),
    )
    url = result["images"][0]["url"]
    raw = urllib.request.urlopen(url).read()
    cleaned = Image.open(BytesIO(raw))

    # Force back onto the original canvas so the overlays align pixel-for-pixel.
    cleaned = cleaned.resize(original.size, Image.LANCZOS)

    IMAGES.mkdir(exist_ok=True)
    fit_16x9(cleaned).save(dest, "JPEG", quality=92)
    print(f"  [{src.stem}] -> {dest.relative_to(IMAGES.parent)}")
    if page_id(src) in BUBBLE_PAGES:
        print("       ^ speech-bubble page -- eyeball this; Kontext may leave bubble edges")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--page", metavar="NN")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    load_dotenv()
    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY not set (see .env).")

    plates = text_plates()
    if args.page:
        pid = args.page.zfill(2)
        plates = [p for p in plates if page_id(p) == pid]
        if not plates:
            sys.exit(f"No spread for page {args.page}")

    for src in plates:
        clean_page(src, args.force)
    print("\nDone. Review images/ before running:  python animate.py zac-is-back")


if __name__ == "__main__":
    main()
