#!/usr/bin/env python3
"""
zac-is-back, step 3: assemble the finished video from the Kling clips.

    composite  clips/page-NN.mp4 + overlays/page-NN-slug.png
                   -> clips-final/page-NN.mp4          (pink verse composited back on)
    stitch     clips-final/*.mp4  (page order)
                   -> zac-is-back.mp4
    --burn-srt zac-is-back.mp4 + zac-is-back.srt
                   -> zac-is-back-captioned.mp4        (otherwise keep the .srt as a sidecar)

Needs ffmpeg on PATH (`sudo apt install ffmpeg`). No fal.ai, no video generation
-- run build_clean.py, `python animate.py zac-is-back`, and build_overlays.py
first.

Usage:
    python build_final.py                    # composite + stitch
    python build_final.py --step composite
    python build_final.py --step stitch
    python build_final.py --page 07 --step composite
    python build_final.py --burn-srt         # also write the captioned cut
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

from zac_lib import (BOOK, CLIPS, CLIPS_FINAL, FINAL, OVERLAYS, SRT, TARGET,
                     page_id, text_plates)

CAPTIONED = BOOK / "zac-is-back-captioned.mp4"
# ASS PrimaryColour is &HAABBGGRR -- this is the lettering pink #C45585.
SRT_STYLE = ("FontName=Comic Sans MS,Fontsize=26,PrimaryColour=&H008554C4,"
             "Outline=0,Shadow=0,Alignment=2,MarginV=48")


def need_ffmpeg() -> None:
    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg not found on PATH. Install it, e.g. `sudo apt install ffmpeg`.")


def ffmpeg(*args: str, cwd: Path | None = None) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args],
        check=True, cwd=cwd,
    )


def composite(only: str | None) -> None:
    CLIPS_FINAL.mkdir(exist_ok=True)
    w, h = TARGET
    for src in text_plates():
        pid = page_id(src)
        if only and pid != only:
            continue
        clip = CLIPS / f"page-{pid}.mp4"
        overlay = OVERLAYS / f"{src.stem}.png"
        out = CLIPS_FINAL / f"page-{pid}.mp4"
        if not clip.exists():
            print(f"  [page-{pid}] no clip yet -- skipping")
            continue
        if not overlay.exists():
            print(f"  [page-{pid}] no overlay -- passing clip through unchanged")
            ffmpeg("-i", str(clip), "-vf", f"scale={w}:{h}",
                   "-c:v", "libx264", "-crf", "18", "-preset", "slow",
                   "-c:a", "copy", str(out))
            continue
        ffmpeg(
            "-i", str(clip), "-i", str(overlay),
            "-filter_complex",
            f"[0:v]scale={w}:{h}[v];[1:v]scale={w}:{h}[o];"
            f"[v][o]overlay=0:0,format=yuv420p[out]",
            "-map", "[out]", "-map", "0:a?",
            "-c:v", "libx264", "-crf", "18", "-preset", "slow", "-c:a", "copy",
            str(out),
        )
        print(f"  [page-{pid}] -> {out.relative_to(BOOK)}")


def stitch() -> None:
    clips = sorted(CLIPS_FINAL.glob("page-*.mp4"))
    if not clips:
        sys.exit("clips-final/ is empty -- run `--step composite` first.")
    listing = CLIPS_FINAL / "_concat.txt"
    listing.write_text("".join(f"file '{c.resolve()}'\n" for c in clips))
    ffmpeg("-f", "concat", "-safe", "0", "-i", str(listing), "-c", "copy", str(FINAL))
    print(f"  -> {FINAL.relative_to(BOOK)}  ({len(clips)} clips)")


def burn_srt() -> None:
    if not SRT.exists():
        sys.exit("zac-is-back.srt not found.")
    if not FINAL.exists():
        sys.exit("zac-is-back.mp4 not found -- stitch first.")
    ffmpeg("-i", FINAL.name,
           "-vf", f"subtitles={SRT.name}:force_style='{SRT_STYLE}'",
           "-c:a", "copy", CAPTIONED.name, cwd=BOOK)
    print(f"  -> {CAPTIONED.relative_to(BOOK)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--step", choices=["composite", "stitch"], default=None)
    ap.add_argument("--page", metavar="NN")
    ap.add_argument("--burn-srt", action="store_true")
    args = ap.parse_args()

    need_ffmpeg()
    only = args.page.zfill(2) if args.page else None

    if args.step in (None, "composite"):
        composite(only)
    if args.step in (None, "stitch") and not only:
        stitch()
    if args.burn_srt:
        burn_srt()
    print("\nDone.")


if __name__ == "__main__":
    main()
