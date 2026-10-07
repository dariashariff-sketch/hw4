"""Typed structures shared by the CC API and the Pydantic AI agent."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

MAX_MESSAGE_CHARS = 2000
MAX_HISTORY_TURNS = 12


# ---------- product cards (what the website renders) ----------

class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """One product as shown on the site. Always built from the DB, never by the LLM."""

    product_id: str
    name: str
    garment_type: str
    category: str
    description: str
    colors: list[str]
    search_tags: list[str]
    image_url: str
    price: float
    inventory: list[SizeStock]
    total_stock: int
    in_stock_sizes: list[str]
    low_stock_sizes: list[str]
    rating: float | None = None
    review_count: int = 0
    bestseller: bool = False


# ---------- chat API (website <-> FastAPI) ----------

class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=MAX_MESSAGE_CHARS * 2)


class PageInfo(BaseModel):
    """What the browser says the shopper is looking at. Untrusted: the backend
    re-checks product_id against the DB before the agent sees anything."""

    path: str = Field(default="/", max_length=200)
    product_id: str | None = Field(default=None, max_length=120)  # set on /products/<id>
    category: str | None = Field(default=None, max_length=60)  # /products?category=...
    search: str | None = Field(default=None, max_length=100)  # /products?q=...
    shelf_title: str | None = Field(default=None, max_length=80)  # chat results currently on the page


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=MAX_MESSAGE_CHARS)
    # Guests: earlier turns from the browser tab, oldest first.
    # Logged-in shoppers: ignored; the server loads their saved history instead.
    history: list[ChatTurn] = Field(default_factory=list)
    page: PageInfo | None = None


MAX_RESULT_CARDS = 30  # largest category (Crewnecks) has 29, so a whole category fits


class ProductMatches(BaseModel):
    """Search results the website shows as animated cards on the page (the results shelf)."""

    title: str = Field(description='Shelf heading, e.g. "Quarter-zips" or "Navy hoodies under $70"')
    products: list[ProductCard]


class ChatReply(BaseModel):
    """What POST /api/chat returns. `results` is null when there's nothing to show on the page."""

    reply: str
    results: ProductMatches | None = None
    saved: bool = False  # True when the turn was stored in the shopper's chat history


class SavedMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    results: ProductMatches | None = None
    created_at: str


class ChatHistory(BaseModel):
    """GET /api/chat/history: the logged-in shopper's saved conversation (empty for guests)."""

    logged_in: bool
    messages: list[SavedMessage] = Field(default_factory=list)


# ---------- tool results (DB -> agent) ----------
# Each tool returns one of these. Every value is copied straight from
# campus_customs.db; the only derived fields (status, totals, size lists) are
# computed in Python so the LLM never has to do arithmetic or judge stock levels.

StockStatus = Literal["in_stock", "low_stock", "sold_out"]


def stock_status(quantity: int, low: int = 5) -> StockStatus:
    if quantity <= 0:
        return "sold_out"
    return "low_stock" if quantity <= low else "in_stock"


class SizeAvailability(BaseModel):
    size: str = Field(description="XS, S, M, L, XL or XXL")
    quantity: int = Field(description="Exact units in stock right now (0 = sold out)")
    status: StockStatus


class ProductSummary(BaseModel):
    """A search hit: enough to recommend an item and pick a follow-up lookup."""

    product_id: str
    name: str
    category: str
    price_usd: float
    colors: list[str]
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]


class SearchResults(BaseModel):
    total_matches: int = Field(description="How many products matched (may exceed the number returned)")
    returned: int
    filters_used: dict[str, str | float]
    ignored_terms: list[str] = Field(
        default_factory=list,
        description="Query words that matched nothing in the catalogue (e.g. a color we don't carry). Tell the shopper honestly.",
    )
    products: list[ProductSummary] = Field(description="Best matches first (ranked by relevance)")


class ProductDetails(BaseModel):
    """Everything the shop knows about one product, including stock for every size."""

    product_id: str
    name: str
    category: str
    garment_type: str
    description: str
    price_usd: float
    colors: list[str]
    sizes: list[SizeAvailability]
    total_in_stock: int
    in_stock_sizes: list[str]
    sold_out_sizes: list[str]
    low_stock_sizes: list[str]


class StockCheck(BaseModel):
    """Answer to "is <product> available in <size>?"."""

    product_id: str
    name: str
    price_usd: float
    size: str = Field(description="Normalized size that was checked, e.g. M")
    quantity: int
    status: StockStatus
    other_sizes_in_stock: list[str] = Field(description="Alternatives to offer if this size is sold out or low")


class ProductNotFound(BaseModel):
    """Returned instead of guessing when an id doesn't exist."""

    error: Literal["product_not_found"] = "product_not_found"
    requested_id: str
    did_you_mean: list[ProductSummary] = Field(description="Closest real products by name, if any")


class InvalidSize(BaseModel):
    error: Literal["invalid_size"] = "invalid_size"
    requested_size: str
    valid_sizes: list[str]


class CategoryInfo(BaseModel):
    name: str
    style_count: int


class ShopperContext(BaseModel):
    """get_shopper_context result: built from ShopDeps (the session), never from chat text."""

    logged_in: bool
    first_name: str | None
    last_name: str | None
    email: str | None
    member_since: str | None
    page_path: str | None
    viewing_product_id: str | None
    viewing_product_name: str | None
    viewing_product_category: str | None
    browsing_category: str | None


# ---------- agent (FastAPI <-> Pydantic AI) ----------

class AgentOutput(BaseModel):
    """The structured answer the agent must return at the end of every turn."""

    reply: str = Field(description="Friendly reply to the shopper, in the Campus Customs voice. Plain text, short.")
    product_ids: list[str] = Field(
        default_factory=list,
        description=(
            "product_id values (exactly as returned by a tool) of the items to show as cards on the page, "
            f"most relevant first, at most {MAX_RESULT_CARDS}. Empty if no products should be shown."
        ),
    )
    results_title: str | None = Field(
        default=None,
        description=(
            "Short heading for the cards on the page, 2-6 words, in Title Case, describing what was searched, "
            'e.g. "Quarter-Zips", "Navy Hoodies In Size M", "Gifts Under $40". Required when product_ids is not empty.'
        ),
    )


@dataclass
class CustomerProfile:
    """The logged-in shopper, as the agent sees them. Deliberately small: no password hash, no ids of other users."""

    user_id: int
    first_name: str
    last_name: str
    email: str
    member_since: str  # date the account was created (YYYY-MM-DD)
    saved_messages: int  # how many chat messages we already remember for them


@dataclass
class PageContext:
    """Where the shopper is on the site, verified against the DB."""

    path: str
    kind: Literal["home", "products", "product", "about", "cart", "account", "login", "signup", "other"]
    product_id: str | None = None  # only set if it's a real product
    product_name: str | None = None
    product_category: str | None = None
    product_garment_type: str | None = None
    product_colors: list[str] | None = None
    product_price_usd: float | None = None
    category: str | None = None
    search: str | None = None
    shelf_title: str | None = None


@dataclass
class ShopDeps:
    """Per-request context handed to the agent's tools and dynamic instructions."""

    customer: CustomerProfile | None = None  # None for guests
    page: PageContext | None = None
