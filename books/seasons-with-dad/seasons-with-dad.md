# Seasons with Dad — notes

By Andrew Abel, illustrated by Graeme Holding. Published 2024, ISBN 9798989431656.
Rhyming picture book celebrating family and nature across spring, summer, autumn,
and winter, set in real locations across Northwest England and North Wales
(Delamere Forest, Helsby Station & Hill, Llangollen Canal, Ffestiniog Railway,
Blackpool, Llandudno, and others — see full list in
`../../../memoriesfond/books/seasons-with-dad.html`).

Full text: `books/seasons-with-dad/book.txt` (gitignored, supplied 2026-07-23).

Source images live in `images/`, named `NN_slug.ext` in the same style as
`finding-granny/images` (not `page-NN-Subject` like adopt-a-dinosaur). The cover
(`01_cover.jpg`) is a 1080x1080 square copied from
`memoriesfond/img/Seasons With Dad - Cover 12.jpg` — hence `requires_outpaint: true`
in metadata.json. Interior illustrations are mostly already wide (~2:1) source
art from the print book, so most pages likely don't need real outpainting —
`04_train-bridge` was animated by copying the original straight into
`images-wide/` unchanged rather than calling the outpaint API.

Renumbered 2026-07-23 after Andrew dropped the duplicate-art pages (old `03`,
`04` bluebell-picking alt, old `11` fishing .jpg — kept the `.png` export,
renamed to `09_fishing`) and the bonus seek-and-find page (old `18`). Pages now
run 01–14 with no gaps. `clips/page-04.mp4` (train bridge) predates this
renumbering and was renamed along with everything else — its `metadata.json`
log entries were updated from page `06` to `04` to match.

Page map (verse stanza → image), current as of the 2026-07-23 renumbering:

- 01: Front cover — files: `01_cover`
- 02: Spring — wildflowers/crocuses/daffodils/bluebells, kids running through
  bluebell woods — files: `02_spring-wildflowers`
- 03: Canal — Dad and boy sitting by a narrowboat — files: `03_canal`
- 04: Steam train — Dad and boy waving from a bridge as a train passes —
  files: `04_train-bridge` (animated)
- 05: Castle — ruined tower, family picnicking on the grass — files: `05_castle`
- 06: Seaside — kids on a bench eating ice cream by the sea wall —
  files: `06_seaside-icecream`
- 07: Seaside — Dad and boy on a donkey ride (same stanza as 06) —
  files: `07_donkey-ride`
- 08: Stargazing — Dad and boy at a bedroom window with a torch, hedgehog and
  moon outside — files: `08_stargazing-hedgehog`
- 09: Fishing — Dad and boy fishing by a river, dragonflies and sticklebacks —
  files: `09_fishing` (.png)
- 10: Duck pond — feeding ducks, swans on the pond — files: `10_duck-pond`
- 11: Autumn — jumping in a leaf pile — files: `11_autumn-leaves`
- 12: Bonfire Night — fireworks and a bonfire — files: `12_bonfire`
- 13: Winter — sledging downhill past a snowman — files: `13_winter-sledging`
- 14: Christmas — family around the table with a cake, tree in the bay window
  — files: `14_christmas-cake`
- 15: Closing stanza — "Seasons with Dad, taking walks, playing games..." —
  Dad, girl, and boy walking together through the woods with a basket —
  files: `15_taking-walks`

**Why:** Andrew supplied the full book text and a folder of loose, oddly-named
source images, which were matched to stanzas and renamed to the
`finding-granny`-style `NN_slug.ext` convention. He then deleted the
duplicate-art pages and the bonus page, so everything was renumbered to close
the gaps and keep the sequence contiguous.

**How to apply:** Use this map for writing/checking motion prompts —
`prompts/NN_slug.md` filenames match `images/` 1:1 now. Confirm aspect ratios
of `05`–`14` before assuming they can all skip outpainting like `04` did.
