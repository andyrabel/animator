"""Shared helpers for the zac-is-back post-production scripts.

Geometry note: the supplied spreads are 2860x1440 (~1.99:1). Everything in the
finished video is aligned to a 1920x1080 (16:9) frame. Both the clean plates and
the lettering overlays are produced with the *same* contain-fit onto that frame
(white bars top/bottom for the clean plate, transparent for the overlay), so an
overlay drops straight onto its clip at overlay=0:0 with no further alignment.
"""
from pathlib import Path

from PIL import Image

BOOK = Path(__file__).parent
IMAGES_TEXT = BOOK / "images-text"    # supplied spreads, verse burned in
IMAGES = BOOK / "images"              # clean plates (JPEG) -> animate.py input
OVERLAYS = BOOK / "overlays"          # transparent lettering PNGs
CLIPS = BOOK / "clips"                # Kling output, page-NN.mp4
CLIPS_FINAL = BOOK / "clips-final"    # clips with the lettering composited back
SRT = BOOK / "zac-is-back.srt"
FINAL = BOOK / "zac-is-back.mp4"

TARGET = (1920, 1080)  # 16:9 frame everything is aligned to


def page_id(path: Path) -> str:
    """'page-03-meet-zac' -> '03'."""
    return path.stem.split("-")[1]


def text_plates() -> list[Path]:
    return sorted(IMAGES_TEXT.glob("page-*.png"))


def _contain_box(src_size: tuple[int, int], target: tuple[int, int] = TARGET):
    (sw, sh), (tw, th) = src_size, target
    scale = min(tw / sw, th / sh)
    nw, nh = round(sw * scale), round(sh * scale)
    return (nw, nh), ((tw - nw) // 2, (th - nh) // 2)


def fit_16x9(img: Image.Image, target: tuple[int, int] = TARGET,
             bg: tuple[int, int, int] = (255, 255, 255)) -> Image.Image:
    """Scale to fit inside `target` (aspect preserved), centre on a solid bg."""
    (nw, nh), off = _contain_box(img.size, target)
    canvas = Image.new("RGB", target, bg)
    canvas.paste(img.convert("RGB").resize((nw, nh), Image.LANCZOS), off)
    return canvas


def fit_16x9_rgba(img: Image.Image, target: tuple[int, int] = TARGET) -> Image.Image:
    """Same framing as fit_16x9 but onto a transparent canvas (alpha kept)."""
    (nw, nh), off = _contain_box(img.size, target)
    resized = img.convert("RGBA").resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", target, (0, 0, 0, 0))
    canvas.paste(resized, off, resized)
    return canvas
