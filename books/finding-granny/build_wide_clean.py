#!/usr/bin/env python3
"""
One-off pipeline for books/finding-granny: strip baked-in story-caption text,
then outpaint to 16:9, writing results to images-wide/.

Pages listed in SKIP_TEXT_REMOVAL keep their text (cover title/credits,
back-cover branding) — only the widescreen outpaint runs for those.
All other pages get FLUX Kontext text removal first (a no-op cost-wise for
pages that never had text, so they're skipped entirely if already text-free
per NO_TEXT_PAGES).

Usage:
    python build_wide_clean.py             # process all pages
    python build_wide_clean.py --page 05    # one page
    python build_wide_clean.py --force      # re-run even if output exists
"""

import argparse
import base64
import os
import sys
import time
from pathlib import Path

import fal_client
from dotenv import load_dotenv
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from animate import calc_outpaint_expansion, download  # noqa: E402

BOOK = Path(__file__).parent
IMAGES = BOOK / "images"
CLEAN = BOOK / "images-clean"
WIDE = BOOK / "images-wide"

# fal-ai/flux-2-pro/outpaint rejects expanded canvases wider than 2560px.
# Source pages are 2588x2625, so anything not already shrunk by Kontext
# (which outputs ~1024x1024) must be downscaled before outpainting.
MAX_SOURCE_HEIGHT = 1400
RETRY_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 5

TEXTREMOVE_ENDPOINT = "fal-ai/flux-pro/kontext"
OUTPAINT_ENDPOINT = "fal-ai/flux-2-pro/outpaint"

TEXT_REMOVE_PROMPT = (
    "Remove all text, words, and speech captions from this children's book "
    "illustration. Keep every character, object, color, and background "
    "exactly as they are. Do not add, move, or restyle anything else."
)

# Pages with no baked-in text — outpaint only, no Kontext call needed.
NO_TEXT_PAGES = {"02", "03", "06", "09", "13", "16"}

# Pages whose text is cover/back-cover branding, not a story caption — keep it.
SKIP_TEXT_REMOVAL = {"01", "21"}


def load_key() -> None:
    load_dotenv()
    if not os.environ.get("FAL_KEY"):
        sys.exit("FAL_KEY not set.")


def image_to_data_url(data: bytes) -> str:
    return f"data:image/jpeg;base64,{base64.b64encode(data).decode()}"


def page_id_of(path: Path) -> str:
    return path.stem.split("_", 1)[0]


def call_with_retry(label: str, fn):
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt == RETRY_ATTEMPTS:
                raise
            print(f"  {label} ERROR (attempt {attempt}/{RETRY_ATTEMPTS}): {exc} — retrying …")
            time.sleep(RETRY_DELAY_SECONDS)


def resize_copy(src: Path, dest: Path, max_height: int) -> None:
    """Downscale src to at most max_height (preserving aspect) and save as dest."""
    with Image.open(src) as img:
        w, h = img.size
        if h > max_height:
            scale = max_height / h
            img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.LANCZOS)
        img.convert("RGB").save(dest, "JPEG", quality=92)


def remove_text(src: Path, dest: Path) -> bool:
    if dest.exists():
        print(f"  [{src.name}] [text-remove] already done — skipping")
        return True
    print(f"  [{src.name}] [text-remove] submitting to fal.ai …", flush=True)
    try:
        result = call_with_retry(
            f"[{src.name}] [text-remove]",
            lambda: fal_client.run(
                TEXTREMOVE_ENDPOINT,
                arguments={
                    "image_url": image_to_data_url(src.read_bytes()),
                    "prompt": TEXT_REMOVE_PROMPT,
                    "output_format": "jpeg",
                },
            ),
        )
        img_url = result["images"][0]["url"]
        download(img_url, dest)
        print(f"  [{src.name}] [text-remove] saved → {dest.relative_to(BOOK)}")
        return True
    except Exception as exc:
        print(f"  [{src.name}] [text-remove] ERROR: {exc}")
        return False


def outpaint(src: Path, dest: Path) -> bool:
    if dest.exists():
        print(f"  [{src.name}] [outpaint] already done — skipping")
        return True
    expand_left, expand_right = calc_outpaint_expansion(src)
    print(
        f"  [{src.name}] [outpaint] +{expand_left}px left, +{expand_right}px right → fal.ai …",
        flush=True,
    )
    try:
        result = call_with_retry(
            f"[{src.name}] [outpaint]",
            lambda: fal_client.run(
                OUTPAINT_ENDPOINT,
                arguments={
                    "image_url": image_to_data_url(src.read_bytes()),
                    "prompt": "children's book illustration, consistent style, extend background only",
                    "expand_left": expand_left,
                    "expand_right": expand_right,
                    "expand_top": 0,
                    "expand_bottom": 0,
                    "output_format": "jpeg",
                },
            ),
        )
        img_url = result["images"][0]["url"]
        download(img_url, dest)
        print(f"  [{src.name}] [outpaint] saved → {dest.relative_to(BOOK)}")
        return True
    except Exception as exc:
        print(f"  [{src.name}] [outpaint] ERROR: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", metavar="NN", help="Process a single page (e.g. 05)")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    load_key()
    CLEAN.mkdir(exist_ok=True)
    WIDE.mkdir(exist_ok=True)

    images = sorted(IMAGES.glob("*.jpg"))
    if args.page:
        pid = args.page.zfill(2)
        images = [p for p in images if page_id_of(p) == pid]
        if not images:
            sys.exit(f"No image found for page {args.page}")

    for src in images:
        pid = page_id_of(src)
        wide_dest = WIDE / src.name
        if wide_dest.exists() and not args.force:
            print(f"  [{src.name}] already have wide output — skipping")
            continue

        clean_dest = CLEAN / src.name
        if args.force and clean_dest.exists():
            clean_dest.unlink()

        if pid in NO_TEXT_PAGES or pid in SKIP_TEXT_REMOVAL:
            if not clean_dest.exists():
                resize_copy(src, clean_dest, MAX_SOURCE_HEIGHT)
        else:
            if not remove_text(src, clean_dest):
                continue
        clean_src = clean_dest

        if args.force and wide_dest.exists():
            wide_dest.unlink()
        outpaint(clean_src, wide_dest)

    print("\nDone.")


if __name__ == "__main__":
    main()
