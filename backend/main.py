"""Campus Customs (CC) backend: FastAPI app for the website and the shopping agent.

Run from the backend/ folder (with the homework 4 .venv active):
    uvicorn main:app --reload --port 8000

- catalog.py   read-only product + inventory queries (shared with the agent)
- auth.py      accounts, password hashing, sessions (/api/auth/*)
- agent.py     Pydantic AI agent wiring (prompt in prompts/prompt.md)
- tools.py     tools the agent can call
- models.py    Pydantic types for chat replies and product cards
"""

import json
import logging
from pathlib import Path

from fastapi import Cookie, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded

import catalog
import audit
import memory
from safety import CRISIS_REPLY, is_crisis
from agent import build_page_context, run_agent, stream_agent
from auth import init_sessions_table, router as auth_router, user_from_token
from models import MAX_RESULT_CARDS, ChatHistory, ChatReply, ChatRequest, CustomerProfile, ProductCard, ProductMatches, ShopDeps

log = logging.getLogger("cc")
UNAVAILABLE = "The shopping assistant is unavailable right now."
LOOP_LIMIT_REPLY = (
    "Sorry, that one took more lookups than I'm allowed for a single question. "
    "Could you narrow it down, for example to one category, size, or price range?"
)
FILTERED_REPLY = (
    "Sorry, I can't help with that one. I'm here to help you find Campus Customs gear, "
    "check sizes, and answer questions about prices and stock. What are you shopping for today?"
)

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
init_sessions_table()
memory.init_memory()
app.include_router(auth_router)
# image_file_path values are relative to data/, e.g. "products/x.jpg". Serve the cleaned
# copies (black backgrounds -> white, made by clean_images.py) when they exist.
app.mount(
    "/media",
    StaticFiles(directory=catalog.CLEAN_IMAGES_DIR if catalog.CLEAN_IMAGES_DIR.is_dir() else catalog.IMAGES_DIR),
    name="media",
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True}


@app.get("/api/categories")
def categories() -> list[dict]:
    return catalog.categories()


@app.get("/api/products", response_model=list[ProductCard])
def list_products(q: str | None = None, category: str | None = None, max_price: float | None = None) -> list[dict]:
    return catalog.search_products(q, category, max_price)


@app.get("/api/products/{product_id}", response_model=ProductCard)
def get_product(product_id: str) -> dict:
    product = catalog.get_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def customer_profile(user: dict) -> CustomerProfile:
    return CustomerProfile(
        user_id=user["id"],
        first_name=user["first_name"],
        last_name=user["last_name"],
        email=user["email"],
        member_since=user["member_since"],
        saved_messages=memory.message_count(user["id"]),
    )


@app.get("/api/chat/history", response_model=ChatHistory)
def chat_history(cc_session: str | None = Cookie(default=None)) -> ChatHistory:
    user = user_from_token(cc_session)
    if not user:
        return ChatHistory(logged_in=False)
    return ChatHistory(logged_in=True, messages=memory.load_for_display(user["id"]))


@app.delete("/api/chat/history")
def clear_chat_history(cc_session: str | None = Cookie(default=None)) -> dict:
    user = user_from_token(cc_session)
    if not user:
        raise HTTPException(status_code=401, detail="Log in to manage your chat history.")
    return {"deleted": memory.clear(user["id"])}


@app.post("/api/chat", response_model=ChatReply)
async def chat(req: ChatRequest, cc_session: str | None = Cookie(default=None)) -> ChatReply:
    """One-shot chat: waits for the whole answer. The widget uses /api/chat/stream instead."""
    user, deps, history = _prepare(req, cc_session)
    if is_crisis(req.message):
        return _finish(user, req.message, _crisis_reply(deps, "chat"))
    try:
        out = await run_agent(req.message, history, deps)
    except UsageLimitExceeded:
        return _finish(user, req.message, ChatReply(reply=LOOP_LIMIT_REPLY))
    except ModelHTTPError as e:
        if _is_filtered(e):
            return _finish(user, req.message, ChatReply(reply=FILTERED_REPLY))
        log.exception("agent run failed")
        raise HTTPException(status_code=502, detail=UNAVAILABLE)
    except Exception:
        log.exception("agent run failed")
        raise HTTPException(status_code=502, detail=UNAVAILABLE)
    return _finish(user, req.message, _to_reply(out))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest, cc_session: str | None = Cookie(default=None)) -> StreamingResponse:
    """Streaming chat (Server-Sent Events). Each event is one `data: {json}` line:
        {"type": "status", "text": "Searching quarter-zips…"}   while the agent works / calls tools
        {"type": "reply", "text": "We've got 11 quarter-…"}     the reply so far (grows as it's written)
        {"type": "done", "reply": ..., "results": ..., "saved": ...}   final ChatReply (same shape as /api/chat)
        {"type": "error", "detail": "..."}
    """
    user, deps, history = _prepare(req, cc_session)

    async def events():
        if is_crisis(req.message):
            reply = _finish(user, req.message, _crisis_reply(deps, "chat_stream"))
            yield _sse({"type": "done", **reply.model_dump()})
            return
        try:
            async for kind, value in stream_agent(req.message, history, deps):
                if kind == "done":
                    reply = _finish(user, req.message, _to_reply(value))
                    yield _sse({"type": "done", **reply.model_dump()})
                else:
                    yield _sse({"type": kind, "text": value})
        except UsageLimitExceeded:
            reply = _finish(user, req.message, ChatReply(reply=LOOP_LIMIT_REPLY))
            yield _sse({"type": "done", **reply.model_dump()})
        except ModelHTTPError as e:
            if _is_filtered(e):
                reply = _finish(user, req.message, ChatReply(reply=FILTERED_REPLY))
                yield _sse({"type": "done", **reply.model_dump()})
            else:
                log.exception("agent stream failed")
                yield _sse({"type": "error", "detail": UNAVAILABLE})
        except Exception:
            log.exception("agent stream failed")
            yield _sse({"type": "error", "detail": UNAVAILABLE})

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _prepare(req: ChatRequest, cc_session: str | None) -> tuple[dict | None, ShopDeps, list]:
    # Who is chatting comes from the session cookie, never from the request body.
    user = user_from_token(cc_session)
    deps = ShopDeps(
        customer=customer_profile(user) if user else None,
        page=build_page_context(req.page),
    )
    # Logged in: the saved conversation is the source of truth (the browser can't rewrite it).
    # Guest: use the transcript the widget sent from this tab.
    history = memory.load_for_agent(user["id"]) if user else req.history
    return user, deps, history


def _crisis_reply(deps: ShopDeps, channel: str) -> ChatReply:
    """Answered before the LLM: the provider's filter could otherwise block the message entirely."""
    audit.start_run()
    shopper = f"user:{deps.customer.user_id}" if deps.customer else "guest"
    audit.record("run_start", channel=channel, shopper=shopper, page=deps.page.path if deps.page else None, message="[crisis message withheld]")
    audit.record("run_end", stop_reason="crisis_guard", requests=0, tool_calls=0, cards=0, reply=audit.short(CRISIS_REPLY))
    return ChatReply(reply=CRISIS_REPLY)


def _is_filtered(e: ModelHTTPError) -> bool:
    # the model provider's safety filter blocked the message (e.g. a jailbreak attempt)
    if "content_filter" in str(e.body):
        log.warning("message blocked by provider content filter")
        return True
    return False


def _to_reply(out) -> ChatReply:
    # The agent only names product_ids; every card is rebuilt from the DB, so a
    # made-up or mistyped id simply doesn't show and prices/stock are always live.
    products = catalog.get_products(out.product_ids)[:MAX_RESULT_CARDS]
    results = None
    if products:
        title = (out.results_title or "").strip() or "Picked for you"
        results = ProductMatches(title=title, products=products)
    return ChatReply(reply=out.reply, results=results)


def _sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _finish(user: dict | None, message: str, reply: ChatReply) -> ChatReply:
    """Save the turn for logged-in shoppers (guests are never stored)."""
    if user:
        memory.save_turn(user["id"], message, reply.reply, reply.results)
        reply.saved = True
    return reply
