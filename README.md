# Animator

Turns children's-book page illustrations into short animated video clips using fal.ai.

## Pipeline

For each page in a book:

1. **outpaint** *(optional, per-book)* — extends a square source JPEG to 16:9 using FLUX 2 Pro Outpaint. Only runs for books with `"requires_outpaint": true` in `metadata.json`.
2. **animate** — submits the 16:9 image plus a motion prompt to Kling v3 Pro image-to-video, producing a ~10s clip.

## Usage

```
python animate.py <book-name>                   # full pipeline, all pages
python animate.py <book-name> --step outpaint    # outpainting only
python animate.py <book-name> --step animate     # animation only
python animate.py <book-name> --page 03          # one page, full pipeline
python animate.py <book-name> --status           # print status table, no API calls
python animate.py <book-name> --force            # re-run even if output exists
```

Requires a `FAL_KEY` in `.env` (see `.env.example` if present, or copy the pattern: `FAL_KEY=...`).

## Book directory structure

Each book lives under `books/<book-name>/` with this layout:

```
books/<book-name>/
  book.txt              # full verse/prose text of the book (gitignored)
  metadata.json          # per-book config + generation log (auto-created/updated by animate.py)
  images/                # source square JPEGs, one per page
  images-wide/           # 16:9 outpainted JPEGs (only if requires_outpaint)
  prompts/                # one .md motion prompt per page
  clips/                  # generated .mp4 clips, one per page
  <book-name>.md          # book-specific notes: page map, characters, visual setting (optional)
```

Page-scoped files (`images/`, `images-wide/`, `prompts/`) share a common filename stem:
`page-NN` or `page-NN-Subject`, e.g. `prompts/page-02-Tyrannosaurus-Rex.md`. `animate.py`
resolves the subject suffix automatically (`find_page_file()` globs `page-{id}-*.{ext}`,
falling back to the exact `page-{id}.{ext}`). Clips are always named plainly: `page-NN.mp4`.

Each prompt file starts with a `# Subject` header line (stripped before being sent to
fal.ai as the actual prompt), followed by the motion-prompt prose.

`metadata.json` schema:

```json
{
  "book": "<book-name>",
  "requires_outpaint": false,
  "cost_per_clip_usd": 1.12,
  "cost_per_outpaint_usd": 0.05,
  "pages": [],
  "generation_log": [ { "page": "00", "step": "animate", "status": "done", "...": "..." } ]
}
```

If missing, `animate.py` creates it with sensible defaults on first run.

## Books

- [`books/adopt-a-dinosaur/`](books/adopt-a-dinosaur/) — 11 pages (00–10)
- [`books/finding-granny/`](books/finding-granny/) — in progress
