"""Read-only access to the CC catalogue and inventory.

Shared by the website API (main.py) and the agent's tools (tools.py), so the
shop pages and the chatbot always see exactly the same prices and stock.
"""

import json
import os
import re
import sqlite3
from pathlib import Path

from search import SearchOutcome, ranked_search

HW4_DIR = Path(__file__).resolve().parent.parent


def _find_data_dir() -> Path:
    """The data pack (campus_customs.db + products/) is NOT in the repo. Look for it in:
    1. $CC_DATA_DIR, if set
    2. hw4/data/           (where the README tells you to place it)
    3. hw4/../data/        (next to the hw4 folder)
    """
    env = os.getenv("CC_DATA_DIR")
    candidates = [Path(env).expanduser()] if env else []
    candidates += [HW4_DIR / "data", HW4_DIR.parent / "data"]
    for c in candidates:
        if (c / "campus_customs.db").exists():
            return c.resolve()
    return candidates[0]  # missing: errors will point at the expected location


DATA_DIR = _find_data_dir()
DB_PATH = DATA_DIR / "campus_customs.db"
IMAGES_DIR = DATA_DIR / "products"
CLEAN_IMAGES_DIR = DATA_DIR / "products_clean"  # made by clean_images.py (white backgrounds)
IMAGE_VERSION = "white-bg-2"

SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
LOW_STOCK = 5  # a size with 1-5 units left counts as "low stock"

# garment_type values in the DB are inconsistent (22 variants), so we map
# them onto a handful of shopper-facing categories. First keyword match wins.
CATEGORY_RULES = [
    ("Quarter-Zips", ["quarter-zip", "1/4 zip"]),
    ("Jackets & Fleece", ["jacket", "fleece"]),
    ("Hoodies", ["hoodie", "hooded"]),
    ("Long Sleeves", ["long-sleeve"]),
    ("Crewnecks", ["crewneck", "mockneck"]),
    ("T-Shirts", ["t-shirt"]),
]
CATEGORY_DISPLAY_ORDER = ["Hoodies", "Crewnecks", "T-Shirts", "Quarter-Zips", "Jackets & Fleece", "Long Sleeves", "Other"]


# Product names in the DB were generated from URL slugs, so punctuation was lost
# ("berkeley-1-4-zip" -> "Berkeley 1 4 Zip"). We clean them up for display only;
# the DB itself is never modified.
NAME_FIXES = [
    (re.compile(r"\b1 4 Zip\b"), "Quarter-Zip"),
    (re.compile(r"\bT Shirt\b"), "T-Shirt"),
    (re.compile(r"\bTri Blend\b"), "Tri-Blend"),
    (re.compile(r"\bFull Zip\b"), "Full-Zip"),
    (re.compile(r"\bL S 2 0\b"), "Long Sleeve 2.0"),
    (re.compile(r"\bVs\b"), "vs."),
    (re.compile(r"^Ua\b"), "UA"),
    (re.compile(r"\bCreqneck\b"), "Crewneck"),
    (re.compile(r" 1$"), ""),  # "Champion Reverse Weave Hoodie 1"
]


def display_name(raw: str) -> str:
    name = raw
    for pattern, replacement in NAME_FIXES:
        name = pattern.sub(replacement, name)
    return name


def connect() -> sqlite3.Connection:
    # read-only so neither the shop API nor the agent can modify the catalogue
    conn = sqlite3.connect(f"file:{DB_PATH.as_posix()}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def categorize(garment_type: str) -> str:
    g = garment_type.lower()
    for category, keywords in CATEGORY_RULES:
        if any(k in g for k in keywords):
            return category
    return "Other"


def _inventory_for(conn: sqlite3.Connection, product_ids: list[str]) -> dict[str, list[dict]]:
    if not product_ids:
        return {}
    marks = ",".join("?" * len(product_ids))
    rows = conn.execute(
        f"SELECT product_id, size, quantity FROM inventory WHERE product_id IN ({marks})",
        product_ids,
    ).fetchall()
    out: dict[str, list[dict]] = {pid: [] for pid in product_ids}
    for r in rows:
        out[r["product_id"]].append({"size": r["size"], "quantity": r["quantity"]})
    for sizes in out.values():
        sizes.sort(key=lambda s: SIZE_ORDER.index(s["size"]) if s["size"] in SIZE_ORDER else 99)
    return out


def _to_product(row: sqlite3.Row, inventory: list[dict]) -> dict:
    return {
        "product_id": row["product_id"],
        "name": display_name(row["name"]),
        "raw_name": row["name"],  # as stored in the DB; kept so searches still match it
        "garment_type": row["garment_type"],
        "category": categorize(row["garment_type"]),
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        # ?v= changes whenever the served images change (e.g. clean_images.py), so browsers
        # drop cached copies of the old black-background photos
        "image_url": f"/media/{Path(row['image_file_path']).name}?v={IMAGE_VERSION}",
        "price": row["price"],
        "inventory": inventory,
        "total_stock": sum(s["quantity"] for s in inventory),
        "in_stock_sizes": [s["size"] for s in inventory if s["quantity"] > 0],
        "low_stock_sizes": [s["size"] for s in inventory if 0 < s["quantity"] <= LOW_STOCK],
        # The DB has no reviews, ratings, or sales data. These stay empty until
        # real data exists; the UI shows "No reviews yet" rather than inventing any.
        "rating": None,
        "review_count": 0,
        "bestseller": False,
    }


def all_products() -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        inv = _inventory_for(conn, [r["product_id"] for r in rows])
    return [_to_product(r, inv[r["product_id"]]) for r in rows]


def get_product(product_id: str) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM catalogue WHERE product_id = ?", (product_id,)).fetchone()
        if row is None:
            return None
        return _to_product(row, _inventory_for(conn, [product_id])[product_id])


def get_products(product_ids: list[str]) -> list[dict]:
    """Products for the given ids, in the given order. Unknown ids are dropped."""
    by_id = {p["product_id"]: p for p in all_products()}
    seen: set[str] = set()
    out = []
    for pid in product_ids:
        if pid in by_id and pid not in seen:
            seen.add(pid)
            out.append(by_id[pid])
    return out


def search_products_ranked(
    q: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
) -> SearchOutcome:
    """Filter by category/price/size, then rank by relevance to the keywords (see search.py)."""
    products = all_products()
    if category:
        products = [p for p in products if p["category"].lower() == category.lower()]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if min_price is not None:
        products = [p for p in products if p["price"] >= min_price]
    if size:
        products = [p for p in products if size.upper() in p["in_stock_sizes"]]
    if q and q.strip():
        return ranked_search(q, products)
    return SearchOutcome(products=products)


def search_products(
    q: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
) -> list[dict]:
    return search_products_ranked(q, category, max_price, min_price, size).products


def categories() -> list[dict]:
    counts: dict[str, int] = {}
    for p in all_products():
        counts[p["category"]] = counts.get(p["category"], 0) + 1
    return [{"name": c, "count": counts[c]} for c in CATEGORY_DISPLAY_ORDER if c in counts]
