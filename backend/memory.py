"""Customer memory: saved chat history for logged-in shoppers (chat_messages table).

Each turn is two rows (role 'user' then 'assistant'). For assistant rows,
products_json stores only the shelf title + product_ids, e.g.
    {"title": "Quarter-Zips", "product_ids": ["berkeley-1-4-zip", ...]}
so reloaded cards are rebuilt from the live catalogue (current prices/stock),
not from a stale snapshot. Older rows saved a full list of product dicts; we
still read those by pulling out their product_id values.

Guests are never written here; their history lives only in the browser tab.
"""

import json
import sqlite3

import catalog
from auth import connect  # writable connection to the same DB
from models import ChatTurn, MAX_HISTORY_TURNS, ProductMatches, SavedMessage

DISPLAY_LIMIT = 50  # messages sent back to the widget on reload


def init_memory() -> None:
    with connect() as conn:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_user ON chat_messages(user_id, id)")


def _parse_products(raw: str | None) -> tuple[str | None, list[str]]:
    if not raw:
        return None, []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None, []
    if isinstance(data, dict):  # current format
        return data.get("title"), [str(i) for i in data.get("product_ids", [])]
    if isinstance(data, list):  # legacy format: full product dicts
        return None, [p["product_id"] for p in data if isinstance(p, dict) and "product_id" in p]
    return None, []


def _rows(conn: sqlite3.Connection, user_id: int, limit: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        "SELECT id, role, content, products_json, created_at FROM chat_messages "
        "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    return list(reversed(rows))


def load_for_agent(user_id: int) -> list[ChatTurn]:
    """The last MAX_HISTORY_TURNS turns as plain text, oldest first, for the LLM."""
    with connect() as conn:
        rows = _rows(conn, user_id, MAX_HISTORY_TURNS)
    turns = []
    for r in rows:
        content = r["content"]
        title, ids = _parse_products(r["products_json"])
        if r["role"] == "assistant" and ids:
            # remind the agent which products it showed, so "the second one" still resolves
            names = [p["name"] for p in catalog.get_products(ids)][:12]
            content += f"\n[Shown on the page{f' as “{title}”' if title else ''}: {', '.join(names)}]"
        turns.append(ChatTurn(role=r["role"], content=content))
    return turns


def load_for_display(user_id: int) -> list[SavedMessage]:
    """Recent messages for the chat widget, with product cards rebuilt from the live DB."""
    with connect() as conn:
        rows = _rows(conn, user_id, DISPLAY_LIMIT)
    out = []
    for r in rows:
        title, ids = _parse_products(r["products_json"])
        products = catalog.get_products(ids) if ids else []
        results = ProductMatches(title=title or "Picked for you", products=products) if products else None
        out.append(SavedMessage(role=r["role"], content=r["content"], results=results, created_at=r["created_at"]))
    return out


def save_turn(user_id: int, user_text: str, reply: str, results: ProductMatches | None) -> None:
    products_json = (
        json.dumps({"title": results.title, "product_ids": [p.product_id for p in results.products]})
        if results
        else None
    )
    with connect() as conn:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)", (user_id, user_text)
        )
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
            (user_id, reply, products_json),
        )


def clear(user_id: int) -> int:
    with connect() as conn:
        return conn.execute("DELETE FROM chat_messages WHERE user_id = ?", (user_id,)).rowcount


def message_count(user_id: int) -> int:
    with connect() as conn:
        return conn.execute("SELECT COUNT(*) FROM chat_messages WHERE user_id = ?", (user_id,)).fetchone()[0]
