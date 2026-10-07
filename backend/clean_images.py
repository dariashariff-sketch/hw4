"""Clean up product photos for the restyled site (Problem 10).

Many photos in data/products/ are cut-outs whose transparent background was
flattened to black, or white photos padded with black side bars. That looks
broken on light cards. This script flood-fills the near-black area that touches
the image border and turns it white, so every product sits on a clean white
background. Dark pixels *inside* the garment are untouched (they aren't
connected to the border).

Originals in data/products/ are never modified; cleaned copies go to
<data pack>/products_clean/, which main.py serves at /media when present.
Like the originals, the cleaned photos stay out of the git repo.

Run from backend/:  python clean_images.py
"""

from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from catalog import CLEAN_IMAGES_DIR, IMAGES_DIR

SRC = IMAGES_DIR
OUT = CLEAN_IMAGES_DIR
DARK = 22  # a border pixel counts as "background black" if all channels are below this
FILL_TOLERANCE = 18  # how far from pure black the flood fill may spread
WHITE = (255, 255, 255)
MARK = (255, 0, 255)  # temporary fill color that never appears in the photos


def clean(path: Path) -> bool:
    original = Image.open(path).convert("RGB")
    im = original.copy()
    w, h = im.size
    px = im.load()
    step = max(1, min(w, h) // 60)
    seeds = [(x, 0) for x in range(0, w, step)] + [(x, h - 1) for x in range(0, w, step)]
    seeds += [(0, y) for y in range(0, h, step)] + [(w - 1, y) for y in range(0, h, step)]
    changed = False
    for x, y in seeds:
        if max(px[x, y]) < DARK:
            ImageDraw.floodfill(im, (x, y), MARK, thresh=FILL_TOLERANCE)
            changed = True
    if not changed:
        original.save(OUT / path.name, quality=90)
        return False
    # background mask = flooded pixels; grow it 1px and feather it so the garment
    # edge blends into white instead of leaving dark speckles
    diff = ImageChops.difference(im, Image.new("RGB", (w, h), MARK)).convert("L")
    mask = diff.point(lambda v: 255 if v == 0 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(1.2))
    Image.composite(Image.new("RGB", (w, h), WHITE), original, mask).save(OUT / path.name, quality=90)
    return True


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    files = sorted(SRC.glob("*.jpg"))
    fixed = sum(clean(f) for f in files)
    print(f"cleaned {fixed} of {len(files)} images -> {OUT}")
