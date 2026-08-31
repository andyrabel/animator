# Zac is Back

Rhyming picture book by Andrew Abel. A gently comic gospel story: a stay-at-home
narrator is pestered all day by a new neighbour, Zac, who keeps coming back for
"one more egg" — one, then two, then three, then four. When Zac finally stops
coming the narrator misses him, goes looking, and finds Zac on the doorstep with
a lemon meringue pie. Over tea Zac shares the gospel; the narrator goes to bed
glad. The next morning the reader learns the running joke's punchline: all those
eggs were for the pie, and Zac has come back to share it "with you".

16 interior spreads, supplied as text-on-artwork PNGs at 2860x1440 (~2:1).
Renamed to the canonical `page-NN-<slug>` stems and moved to **`images-text/`**
(these keep the burned-in verse — reference for the SRT and the overlays).

## Text handling (decided)

The verse is **burned into every supplied spread** (pink hand-lettered font,
placement varies — usually the left page, sometimes the right, sometimes a
speech bubble over Zac). Kling would warp burned-in lettering during animation,
so:

1. `book.txt` — full verse transcribed from the spreads (source of truth). ✅
2. `zac-is-back.srt` — the same verse as a caption track (house pattern, cf.
   `finding-granny`). ✅ 27 cues, 10 s per spread, double-stanza spreads split
   into sub-cues. Total runtime 02:40 (16 × 10 s). Re-time if a voiceover or a
   different clip length is used.
3. `images-text/` — supplied spreads, renamed, verse still burned in. ✅
4. `images/` — clean plates, all lettering removed, `page-NN-<slug>.jpg`,
   1920×1080 (letterboxed on white). This is what `animate.py` reads.
   **Note:** `animate.py` only globs `images/page-*.jpg` (not `.png`), so the
   clean plates must be JPEG. `metadata.json` has `requires_outpaint: false`,
   so `images/` feeds Kling directly. **Built by `build_clean.py`** (FLUX
   Kontext) — TODO, ~$0.64 on fal.ai.
5. `overlays/` — the pink hand-lettering as transparent 1920×1080 PNGs,
   composited back onto each clip. **First pass built by `build_overlays.py`**
   (colour key, no cost) ✅ — pages 06/08/12/16 flagged for a hand pass: their
   verse sat in a translucent white panel over artwork, and the bare keyed text
   may need that panel painted back for legibility (or leave those lines to the
   SRT only).

Prompts are written against the **clean plate** and every prompt forbids the
model from rendering any text.

### Post-production scripts (run from `books/zac-is-back/`)

| Script | Does | Cost |
|--------|------|------|
| `build_clean.py`    | `images-text/*.png` → Kontext text removal → `images/*.jpg` (1920×1080) | ~$0.04/page fal.ai |
| *(then)* `python ../../animate.py zac-is-back` | `images/*.jpg` → Kling → `clips/page-NN.mp4` | ~$1.12/page fal.ai |
| `build_overlays.py` | `images-text/*.png` → colour-key the pink verse → `overlays/*.png` | free (Pillow) |
| `build_final.py`    | `clips/` + `overlays/` → `clips-final/` → `zac-is-back.mp4`; `--burn-srt` for the captioned cut | free (needs `ffmpeg`) |

`zac_lib.py` holds the shared 1920×1080 contain-fit so clean plates and overlays
register pixel-for-pixel. `ffmpeg` is not yet installed on this machine
(`sudo apt install ffmpeg`).

## Visual style — mixed media, keep it that way

Every spread combines three looks. Do **not** let the video model unify or
restyle them:

- **Room / set:** loose, hand-drawn black-ink line art on plain white — doors,
  curtained windows, staircase, kitchen rail. Wobbly "live sketch" quality.
- **Zac:** a soft-rendered 3D fuzzy puppet (Grover-ish). Bright blue fur, round
  wood-rimmed glasses, big pink ball nose, wide pink mouth, blue-and-white
  horizontal-striped shirt. Always cheerful.
- **Food props:** photographic — brown eggs, a basket of eggs, a toasted lemon
  meringue pie. Plus some flat vector props: cream/gold teacups + teapot, lemons,
  a flour bag, the narrator's armchair and beret.

## The narrator ("I" / "me")

Never shown as a face. Only ever the **back of a dusty-pink armchair** (white
dash texture) and a **navy beret**, low in the frame. Keep it that way in every
clip — no reveal.

## Zac — character continuity

Zac must read as the **same puppet** in every clip he appears in. Canonical Zac,
from the supplied artwork:

- Bright blue shaggy fur; soft-rendered 3D puppet (Grover family).
- Round **wood-rimmed** glasses, perfectly circular lenses.
- Big pink ball nose, centred.
- Wide pink mouth, always an open cheerful grin.
- Blue-and-white **horizontal**-striped crew shirt; blue furry hands, striped cuff.
- Body language: bouncy, delighted, guileless.

Never restyle, recolour, re-proportion, or "cartoon-flatten" him, and never blend
him into the black-ink line-art of the room.

### Staged face reveal — pages 01–03 (do not break)

The reader does not see Zac's face until page 03. Hold this exactly:

| Page | How much of Zac we see | Forbidden |
|------|------------------------|-----------|
| 01 | **Side of his head only** — a blue profile passing left-to-right behind the window. Ear, back of head, edge of glasses, tip of the pink nose in silhouette. Moving through, not stopping. | No front view, no eye contact, no full face. |
| 02 | **One hand and striped cuff only**, reaching in through the part-open door. | No arm past the wrist, no head, no face, no body. |
| 03 | **Full face, front on — the big reveal.** First and only time we see all of Zac at once. Let it land: he fills the left half, beams straight out. | Nothing withheld now; this is the payoff of 01–02. |

From page 04 on, Zac is shown freely (full puppet, any angle).

## Page map

Stems below are the shared filename stem for `images-text/`, `images/` (clean),
`prompts/`, and `overlays/`. Clips are always `clips/page-NN.mp4`.

| Page | Stem | Spread caption | Beat |
|------|------|----------------|------|
| 01 | `page-01-sitting-around`     | I was sitting around      | Narrator in armchair; doorbell rings |
| 02 | `page-02-opened-the-door`    | I opened the door         | Door opens; a blue hand reaches in |
| 03 | `page-03-meet-zac`           | Hi, I'm Zac               | Zac introduces himself |
| 04 | `page-04-one-egg`            | He asked for an egg       | Asks politely for one egg, runs off |
| 05 | `page-05-now-two`            | Now he wants two          | Back again — wants two |
| 06 | `page-06-now-three`          | This time he wants three  | Back again — wants three; doorbell switched off |
| 07 | `page-07-now-four`           | Now he wants four         | Knocks, says sorry — wants four |
| 08 | `page-08-missed-him`         | For the rest of the day   | Zac stops coming; narrator misses him |
| 09 | `page-09-one-last-try`       | At the end of the day     | Sunset; narrator goes to check one last time |
| 10 | `page-10-lemon-meringue-pie` | And there he stood with   | Zac on the step with a lemon meringue pie |
| 11 | `page-11-cup-of-tea`         | For a warm cup of tea     | Tea together, talking |
| 12 | `page-12-gods-love`          | He spoke of God's love    | Zac shares the gospel; three crosses at sunrise |
| 13 | `page-13-headed-to-bed`      | As I headed to bed        | Narrator climbs the stairs, glad |
| 14 | `page-14-all-those-eggs`     | One thing still bugged me | Puzzling over what Zac did with the eggs |
| 15 | `page-15-lots-of-eggs`       | You need lots of eggs for | Kitchen + recipe card — it was for the pie |
| 16 | `page-16-share-it-with-you`  | To share it with you      | "So much pie left" — Zac comes to share it |

Note: pages 10 and 15 both land on "...a lemon meringue pie!" — deliberate,
it's the setup and the payoff of the running joke.

## Clip length

10 seconds per clip (project default across all books).
