#!/usr/bin/env python3
"""
Animate children's book pages using fal.ai.

Pipeline (per book, steps are skippable):
  1. outpaint  — extend square JPEGs to 16:9 using FLUX 2 Pro Outpaint
                 (only for books with "requires_outpaint": true in metadata.json)
  2. animate   — submit 16:9 images to Kling v3 Pro image-to-video

Usage:
    python animate.py <book-name>                    # full pipeline
    python animate.py <book-name> --step outpaint    # outpainting only
    python animate.py <book-name> --step animate     # Kling generation only
    python animate.py <book-name> --page 03          # one page, full pipeline
    python animate.py <book-name> --status           # print status table, no API calls
    python animate.py <book-name> --force            # re-run even if output exists
"""

import argparse
import base64
import json
import math
import os
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import fal_client
from dotenv import load_dotenv

OUTPAINT_ENDPOINT = "fal-ai/flux-2-pro/outpaint"
ANIMATE_ENDPOINT = "fal-ai/kling-video/v3/pro/image-to-video"

ANIMATE_DURATION = "5"
ANIMATE_ASPECT_RATIO = "16:9"

COST_ANIMATE_USD = 0.14   # Kling v3 Pro, 5 s
COST_OUTPAINT_USD = 0.05  # FLUX 2 Pro Outpaint, ~1.8 MP


# ---------------------------------------------------------------------------
# Environment / metadata helpers
# ---------------------------------------------------------------------------

def load_key() -> None:
    load_dotenv()
    if not os.environ.get("FAL_KEY"):
        sys.exit(
            "FAL_KEY not set.\n"
            "Copy .env.example to .env and add your key, then re-run."
        )


def book_dir(book_name: str) -> Path:
    root = Path(__file__).parent / "books" / book_name
    if not root.exists():
        sys.exit(f"Book directory not found: {root}")
    return root


def load_metadata(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text())
    return {
        "book": path.parent.name,
        "requires_outpaint": False,
        "cost_per_clip_usd": COST_ANIMATE_USD,
        "cost_per_outpaint_usd": COST_OUTPAINT_USD,
        "pages": [],
        "generation_log": [],
    }


def save_metadata(path: Path, meta: dict) -> None:
    path.write_text(json.dumps(meta, indent=2))


def latest_status(meta: dict) -> dict[str, dict[str, str]]:
    """Return {page_id: {step: status}} using the latest log entry per (page, step)."""
    result: dict[str, dict[str, str]] = {}
    for entry in meta.get("generation_log", []):
        pid = entry["page"]
        step = entry.get("step", "animate")
        result.setdefault(pid, {})[step] = entry["status"]
    return result


def log_entry(meta: dict, page_id: str, step: str, status: str, **kwargs) -> None:
    entry = {
        "page": page_id,
        "step": step,
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **kwargs,
    }
    meta.setdefault("generation_log", []).append(entry)


def image_to_data_url(image_path: Path) -> str:
    data = image_path.read_bytes()
    b64 = base64.b64encode(data).decode()
    return f"data:image/jpeg;base64,{b64}"


def download(url: str, dest: Path) -> None:
    urllib.request.urlretrieve(url, dest)


# ---------------------------------------------------------------------------
# Outpainting step
# ---------------------------------------------------------------------------

def calc_outpaint_expansion(image_path: Path) -> tuple[int, int]:
    """
    Return (expand_left, expand_right) pixel counts to reach 16:9 from a
    square source. Uses Pillow to read the actual image dimensions.
    """
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            w, h = img.size
    except ImportError:
        # Fall back: assume image is square and use file size heuristic
        # This path is a last resort — install Pillow for accuracy.
        w = h = 1024

    if w != h:
        # Already non-square — compute expansion from actual dimensions
        target_w = int(math.ceil(h * 16 / 9))
    else:
        target_w = int(math.ceil(w * 16 / 9))

    extra = target_w - w
    expand_left = extra // 2
    expand_right = extra - expand_left  # absorbs any odd pixel
    return expand_left, expand_right


def outpaint_page(book: Path, page_id: str, meta: dict, meta_path: Path, force: bool) -> bool:
    src = book / "images" / f"page-{page_id}.jpg"
    dest = book / "images-wide" / f"page-{page_id}.jpg"

    if not src.exists():
        print(f"  [{page_id}] [outpaint] skip — source image not found")
        return False

    if dest.exists() and not force:
        print(f"  [{page_id}] [outpaint] already done — skipping")
        return True

    expand_left, expand_right = calc_outpaint_expansion(src)
    print(
        f"  [{page_id}] [outpaint] +{expand_left}px left, +{expand_right}px right → fal.ai …",
        flush=True,
    )

    try:
        result = fal_client.run(
            OUTPAINT_ENDPOINT,
            arguments={
                "image_url": image_to_data_url(src),
                "prompt": "children's book illustration, consistent style, extend background only",
                "expand_left": expand_left,
                "expand_right": expand_right,
                "expand_top": 0,
                "expand_bottom": 0,
                "output_format": "jpeg",
            },
        )

        img_url = result["images"][0]["url"]
        download(img_url, dest)
        print(f"  [{page_id}] [outpaint] saved → {dest.relative_to(Path.cwd())}")
        log_entry(meta, page_id, "outpaint", "done", cost_usd=COST_OUTPAINT_USD, output=str(dest))
        save_metadata(meta_path, meta)
        return True

    except Exception as exc:
        print(f"  [{page_id}] [outpaint] ERROR: {exc}")
        log_entry(meta, page_id, "outpaint", "error", error=str(exc))
        save_metadata(meta_path, meta)
        return False


# ---------------------------------------------------------------------------
# Animation step
# ---------------------------------------------------------------------------

def animate_page(book: Path, page_id: str, meta: dict, meta_path: Path, force: bool) -> bool:
    requires_outpaint = meta.get("requires_outpaint", False)
    if requires_outpaint:
        image_path = book / "images-wide" / f"page-{page_id}.jpg"
        if not image_path.exists():
            print(f"  [{page_id}] [animate] skip — wide image missing (run outpaint first)")
            return False
    else:
        image_path = book / "images" / f"page-{page_id}.jpg"
        if not image_path.exists():
            print(f"  [{page_id}] [animate] skip — source image not found")
            return False

    prompt_path = book / "prompts" / f"page-{page_id}.txt"
    if not prompt_path.exists():
        print(f"  [{page_id}] [animate] skip — prompt file not found")
        return False

    clip_path = book / "clips" / f"page-{page_id}.mp4"
    if clip_path.exists() and not force:
        print(f"  [{page_id}] [animate] already done — skipping")
        return True

    prompt = prompt_path.read_text().strip()
    print(f"  [{page_id}] [animate] submitting to fal.ai …", flush=True)

    try:
        result = fal_client.run(
            ANIMATE_ENDPOINT,
            arguments={
                "image_url": image_to_data_url(image_path),
                "prompt": prompt,
                "duration": ANIMATE_DURATION,
                "aspect_ratio": ANIMATE_ASPECT_RATIO,
            },
        )

        video_url = result["video"]["url"]
        download(video_url, clip_path)
        print(f"  [{page_id}] [animate] saved → {clip_path.relative_to(Path.cwd())}")
        log_entry(meta, page_id, "animate", "done", cost_usd=COST_ANIMATE_USD, clip=str(clip_path))
        save_metadata(meta_path, meta)
        return True

    except Exception as exc:
        print(f"  [{page_id}] [animate] ERROR: {exc}")
        log_entry(meta, page_id, "animate", "error", error=str(exc))
        save_metadata(meta_path, meta)
        return False


# ---------------------------------------------------------------------------
# Status display
# ---------------------------------------------------------------------------

def print_status(book: Path, meta: dict) -> None:
    requires_outpaint = meta.get("requires_outpaint", False)
    statuses = latest_status(meta)
    images = sorted((book / "images").glob("page-*.jpg"))

    if not images:
        print("No source images found in images/")
        return

    done_outpaint = 0
    done_animate = 0

    if requires_outpaint:
        print(f"\n{'PAGE':<8} {'SRC':<6} {'WIDE':<6} {'PROMPT':<8} {'CLIP':<6} {'OUTPAINT':<12} ANIMATE")
        print("-" * 68)
    else:
        print(f"\n{'PAGE':<8} {'SRC':<6} {'PROMPT':<8} {'CLIP':<6} ANIMATE")
        print("-" * 42)

    for img in images:
        pid = img.stem.replace("page-", "")
        page_status = statuses.get(pid, {})
        has_wide = (book / "images-wide" / f"page-{pid}.jpg").exists()
        has_prompt = (book / "prompts" / f"page-{pid}.txt").exists()
        has_clip = (book / "clips" / f"page-{pid}.mp4").exists()
        op_status = page_status.get("outpaint", "pending")
        an_status = page_status.get("animate", "pending")

        if op_status == "done":
            done_outpaint += 1
        if an_status == "done":
            done_animate += 1

        if requires_outpaint:
            print(
                f"  {pid:<6} {'yes':<6} {'yes' if has_wide else 'no':<6} "
                f"{'yes' if has_prompt else 'NO':<8} {'yes' if has_clip else 'no':<6} "
                f"{op_status:<12} {an_status}"
            )
        else:
            print(
                f"  {pid:<6} {'yes':<6} {'yes' if has_prompt else 'NO':<8} "
                f"{'yes' if has_clip else 'no':<6} {an_status}"
            )

    total = len(images)
    outpaint_cost = done_outpaint * meta.get("cost_per_outpaint_usd", COST_OUTPAINT_USD)
    animate_cost = done_animate * meta.get("cost_per_clip_usd", COST_ANIMATE_USD)
    total_cost = outpaint_cost + animate_cost

    print()
    if requires_outpaint:
        print(f"Outpaint:  {done_outpaint}/{total} done  (${outpaint_cost:.2f})")
    print(f"Animate:   {done_animate}/{total} done  (${animate_cost:.2f})")
    print(f"Total cost so far: ${total_cost:.2f}")

    remaining_animate = total - done_animate
    if remaining_animate:
        est = remaining_animate * meta.get("cost_per_clip_usd", COST_ANIMATE_USD)
        if requires_outpaint:
            remaining_outpaint = total - done_outpaint
            est += remaining_outpaint * meta.get("cost_per_outpaint_usd", COST_OUTPAINT_USD)
        print(f"Est. remaining: ${est:.2f}")
    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Animate book pages with fal.ai.")
    parser.add_argument("book", help="Book folder name under books/")
    parser.add_argument(
        "--step",
        choices=["outpaint", "animate"],
        default=None,
        help="Run only one pipeline step (default: run all applicable steps)",
    )
    parser.add_argument("--page", metavar="NN", help="Process a single page (e.g. 03)")
    parser.add_argument("--status", action="store_true", help="Print status table and exit")
    parser.add_argument("--force", action="store_true", help="Re-run steps even if output exists")
    args = parser.parse_args()

    book = book_dir(args.book)
    meta_path = book / "metadata.json"
    meta = load_metadata(meta_path)

    if args.status:
        print_status(book, meta)
        return

    load_key()

    requires_outpaint = meta.get("requires_outpaint", False)

    run_outpaint = requires_outpaint and args.step in (None, "outpaint")
    run_animate = args.step in (None, "animate")

    if args.step == "outpaint" and not requires_outpaint:
        sys.exit(f"Book '{args.book}' does not require outpainting (requires_outpaint is false in metadata.json).")

    if args.page:
        pages = [args.page.zfill(2)]
    else:
        images = sorted((book / "images").glob("page-*.jpg"))
        pages = [img.stem.replace("page-", "") for img in images]

    if not pages:
        print("No pages to process. Add JPEGs to images/ first.")
        return

    steps_label = " + ".join(filter(None, ["outpaint" if run_outpaint else None, "animate" if run_animate else None]))
    print(f"\nBook: {args.book}  |  Steps: {steps_label}  |  Pages: {len(pages)}\n")

    outpaint_ok = 0
    animate_ok = 0

    for pid in pages:
        if run_outpaint:
            ok = outpaint_page(book, pid, meta, meta_path, args.force)
            if ok:
                outpaint_ok += 1

        if run_animate:
            ok = animate_page(book, pid, meta, meta_path, args.force)
            if ok:
                animate_ok += 1

    print(f"\nDone.")
    if run_outpaint:
        print(f"  Outpainted: {outpaint_ok}/{len(pages)}")
    if run_animate:
        print(f"  Animated:   {animate_ok}/{len(pages)}")

    print()
    print_status(book, meta)


if __name__ == "__main__":
    main()
