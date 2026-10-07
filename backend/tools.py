"""Tools the CC shopping agent can call. Every fact about products, prices, and
stock must come through one of these, which read data/campus_customs.db.

Each tool returns a typed model from models.py. Values are copied straight from
the DB; derived fields (stock status, totals, size lists) are computed here so
the LLM never has to count, add, or judge "low stock" itself.
"""

import difflib

from pydantic_ai import RunContext

import catalog
from audit import audited
from models import (
    CategoryInfo,
    InvalidSize,
    ProductDetails,
    ProductNotFound,
    ProductSummary,
    SearchResults,
    ShopperContext,
    ShopDeps,
    SizeAvailability,
    StockCheck,
    stock_status,
)

MAX_RESULTS = 30  # matches MAX_RESULT_CARDS so a whole category can go on the page

# shoppers say "medium", "2XL", "extra large"...; the DB uses XS-XXL
SIZE_ALIASES = {
    "XS": "XS", "XSMALL": "XS", "EXTRASMALL": "XS",
    "S": "S", "SM": "S", "SMALL": "S",
    "M": "M", "MD": "M", "MED": "M", "MEDIUM": "M",
    "L": "L", "LG": "L", "LARGE": "L",
    "XL": "XL", "XLARGE": "XL", "EXTRALARGE": "XL",
    "XXL": "XXL", "2XL": "XXL", "XXLARGE": "XXL", "2XLARGE": "XXL", "EXTRAEXTRALARGE": "XXL",
}


def normalize_size(size: str) -> str | None:
    key = "".join(ch for ch in size.upper() if ch.isalnum())
    return SIZE_ALIASES.get(key)


def _summary(p: dict) -> ProductSummary:
    return ProductSummary(
        product_id=p["product_id"],
        name=p["name"],
        category=p["category"],
        price_usd=p["price"],
        colors=p["colors"],
        in_stock_sizes=p["in_stock_sizes"],
        sold_out_sizes=[s["size"] for s in p["inventory"] if s["quantity"] == 0],
    )


def _not_found(product_id: str) -> ProductNotFound:
    products = catalog.all_products()
    by_key = {p["product_id"]: p for p in products} | {p["name"].lower(): p for p in products}
    close = difflib.get_close_matches(product_id.lower(), list(by_key), n=3, cutoff=0.5)
    seen, hits = set(), []
    for key in close:
        p = by_key[key]
        if p["product_id"] not in seen:
            seen.add(p["product_id"])
            hits.append(_summary(p))
    return ProductNotFound(requested_id=product_id, did_you_mean=hits)


def search_products(
    ctx: RunContext[ShopDeps],
    query: str | None = None,
    category: str | None = None,
    max_price: float | None = None,
    min_price: float | None = None,
    size: str | None = None,
) -> SearchResults | InvalidSize:
    """Find products in the Campus Customs catalogue. Use this first to discover product_ids.

    Args:
        query: Keywords in the shopper's own words, e.g. "navy hoodie", "bulldog", "saybrook",
            "gift for my grandpa", "quarterzip". Synonyms, plurals and small typos are handled and
            results come back ranked by relevance. Leave empty to browse.
        category: One of Hoodies, Crewnecks, T-Shirts, Quarter-Zips, Jackets & Fleece, Long Sleeves.
        max_price: Only items at or below this USD price.
        min_price: Only items at or above this USD price.
        size: Only items with this size currently in stock (XS, S, M, L, XL, XXL; "medium" etc. also work).
    """
    norm_size = None
    if size:
        norm_size = normalize_size(size)
        if norm_size is None:
            return InvalidSize(requested_size=size, valid_sizes=catalog.SIZE_ORDER)
    outcome = catalog.search_products_ranked(query, category, max_price, min_price, norm_size)
    results = outcome.products
    filters = {k: v for k, v in {
        "query": query, "category": category, "max_price": max_price, "min_price": min_price, "size": norm_size,
    }.items() if v not in (None, "")}
    return SearchResults(
        total_matches=len(results),
        returned=min(len(results), MAX_RESULTS),
        filters_used=filters,
        ignored_terms=outcome.ignored_terms,
        products=[_summary(p) for p in results[:MAX_RESULTS]],
    )


def get_product_details(ctx: RunContext[ShopDeps], product_id: str) -> ProductDetails | ProductNotFound:
    """Full facts for one product: description, price, colors, and exact stock for every size.
    Call this before describing an item in detail or answering "what sizes do you have?".

    Args:
        product_id: The product_id exactly as returned by search_products.
    """
    p = catalog.get_product(product_id)
    if p is None:
        return _not_found(product_id)
    sizes = [
        SizeAvailability(size=s["size"], quantity=s["quantity"], status=stock_status(s["quantity"], catalog.LOW_STOCK))
        for s in p["inventory"]
    ]
    return ProductDetails(
        product_id=p["product_id"],
        name=p["name"],
        category=p["category"],
        garment_type=p["garment_type"],
        description=p["description"],
        price_usd=p["price"],
        colors=p["colors"],
        sizes=sizes,
        total_in_stock=p["total_stock"],
        in_stock_sizes=[s.size for s in sizes if s.status != "sold_out"],
        sold_out_sizes=[s.size for s in sizes if s.status == "sold_out"],
        low_stock_sizes=[s.size for s in sizes if s.status == "low_stock"],
    )


def check_stock(ctx: RunContext[ShopDeps], product_id: str, size: str) -> StockCheck | ProductNotFound | InvalidSize:
    """Check live stock of one product in one size. Use for "do you have X in size M?" or "how many are left?".

    Args:
        product_id: The product_id exactly as returned by search_products.
        size: The size to check: XS, S, M, L, XL or XXL ("medium", "2XL" etc. are accepted).
    """
    norm = normalize_size(size)
    if norm is None:
        return InvalidSize(requested_size=size, valid_sizes=catalog.SIZE_ORDER)
    p = catalog.get_product(product_id)
    if p is None:
        return _not_found(product_id)
    qty = next((s["quantity"] for s in p["inventory"] if s["size"] == norm), 0)
    return StockCheck(
        product_id=p["product_id"],
        name=p["name"],
        price_usd=p["price"],
        size=norm,
        quantity=qty,
        status=stock_status(qty, catalog.LOW_STOCK),
        other_sizes_in_stock=[s for s in p["in_stock_sizes"] if s != norm],
    )


def get_shopper_context(ctx: RunContext[ShopDeps]) -> ShopperContext:
    """Who you're chatting with and which page they're on right now (from the session, not the shopper's words).
    Use it when they say "this"/"it" and you're unsure which product they mean, or ask "who am I logged in as?"."""
    c, p = ctx.deps.customer, ctx.deps.page
    return ShopperContext(
        logged_in=c is not None,
        first_name=c.first_name if c else None,
        last_name=c.last_name if c else None,
        email=c.email if c else None,
        member_since=c.member_since if c else None,
        page_path=p.path if p else None,
        viewing_product_id=p.product_id if p else None,
        viewing_product_name=p.product_name if p else None,
        viewing_product_category=p.product_category if p else None,
        browsing_category=p.category if p else None,
    )


def list_categories(ctx: RunContext[ShopDeps]) -> list[CategoryInfo]:
    """The shop's product categories and how many styles each has."""
    return [CategoryInfo(name=c["name"], style_count=c["count"]) for c in catalog.categories()]


# every tool call + result is written to output/audit_trail.json (see audit.py)
TOOLS = [audited(t) for t in (search_products, get_product_details, check_stock, list_categories, get_shopper_context)]
