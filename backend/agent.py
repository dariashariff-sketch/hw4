"""Wires up the Campus Customs shopping agent (Pydantic AI).

- System prompt: prompts/prompt.md (read once at startup)
- Model: gpt-5.6-luna via the Portkey OpenAI-compatible gateway; override with CC_MODEL
- Tools: tools.py
- Context: ShopDeps (customer profile + verified page context) -> dynamic instructions
- Output: models.AgentOutput (reply text + product_ids to show as cards)
"""

import os
import time

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent, RunContext
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
import catalog
from models import MAX_HISTORY_TURNS, AgentOutput, ChatTurn, CustomerProfile, PageContext, PageInfo, ShopDeps
from tools import TOOLS

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
# the course keeps PORTKEY_API_KEY in the .env at the workspace root (foundations of AI/.env)
# PORTKEY_API_KEY: use hw4/.env if present, otherwise the nearest .env in a parent folder
# (the course keeps one at the workspace root). Never committed; see .env.example.
for _folder in [BACKEND_DIR.parent, *BACKEND_DIR.parent.parents]:
    if (_folder / ".env").is_file():
        load_dotenv(_folder / ".env")
        break

PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
MODEL_NAME = os.getenv("CC_MODEL", "gpt-5.6-luna")


def _build_model() -> OpenAIChatModel:
    key = os.getenv("PORTKEY_API_KEY")
    if not key:
        raise RuntimeError("PORTKEY_API_KEY is not set. Add it to the .env file at the workspace root.")
    return OpenAIChatModel(MODEL_NAME, provider=OpenAIProvider(base_url=PORTKEY_BASE_URL, api_key=key))


@lru_cache(maxsize=1)
def get_agent() -> Agent[ShopDeps, AgentOutput]:
    """Built on first use, so the website still serves products if the key is missing."""
    agent = Agent(
        _build_model(),
        deps_type=ShopDeps,
        output_type=AgentOutput,
        instructions=PROMPT_PATH.read_text(encoding="utf-8"),
        tools=TOOLS,
        retries=2,
    )

    # Dynamic instructions: rebuilt from ShopDeps on every run, appended after prompt.md.
    @agent.instructions
    def customer_context(ctx: RunContext[ShopDeps]) -> str:
        return describe_customer(ctx.deps.customer)

    @agent.instructions
    def page_context(ctx: RunContext[ShopDeps]) -> str:
        return describe_page(ctx.deps.page)

    return agent


# ---------- agent context: who is chatting, and what page they're on ----------

def describe_customer(c: CustomerProfile | None) -> str:
    if c is None:
        return (
            "## Who you're talking to\n"
            "A guest who is not logged in. You don't know their name or email. Their chat is not saved; "
            "if they want you to remember them next time, they can log in or create an account."
        )
    memory = (
        f"You remember {c.saved_messages} earlier messages with them (shown as the conversation history)."
        if c.saved_messages
        else "This is their first chat with you."
    )
    return (
        "## Who you're talking to\n"
        f"A logged-in customer: {c.first_name} {c.last_name}, email {c.email}, member since {c.member_since}. "
        f"{memory} Their chat history is saved to their account.\n"
        "Use their first name naturally (not in every message). Only share their email if they ask what "
        "account they're logged in with. You have no access to their password, payment details, or orders."
    )


def describe_page(p: PageContext | None) -> str:
    if p is None:
        return "## What's on their screen\nUnknown."
    lines = ["## What's on their screen", f"Page: {p.path} ({p.kind})."]
    if p.product_id:
        colors = ", ".join(p.product_colors or [])
        lines.append(
            f"They are viewing the product page for **{p.product_name}** (product_id `{p.product_id}`), "
            f"a {p.product_garment_type} in the {p.product_category} category, ${p.product_price_usd:g}, "
            f"colors listed: {colors}."
        )
        lines.append(
            'When they say "this", "it", "this one" or ask about a color/size without naming a product, they mean '
            f"{p.product_name}. Check its live stock with tools (check_stock / get_product_details) using that product_id. "
            "If they ask for a color that isn't in its colors, say this item doesn't come in that color, then offer "
            f"similar {p.product_category} that do (search for them) rather than switching to a different kind of garment."
        )
    if p.category:
        lines.append(f"They are browsing the {p.category} category.")
    if p.search:
        lines.append(f'They searched the products page for "{p.search}".')
    if p.shelf_title:
        lines.append(f'Your earlier results "{p.shelf_title}" are currently shown at the top of their page.')
    return "\n".join(lines)


PAGE_KINDS = {"": "home", "products": "products", "about": "about", "cart": "cart",
              "account": "account", "login": "login", "signup": "signup"}


def build_page_context(page: PageInfo | None) -> PageContext | None:
    """Turn the browser's PageInfo into trusted context. Product facts come from the DB, not the client."""
    if page is None:
        return None
    parts = [x for x in page.path.split("?")[0].split("/") if x]
    kind = PAGE_KINDS.get(parts[0] if parts else "", "other")
    ctx = PageContext(path=page.path, kind=kind, search=page.search, shelf_title=page.shelf_title)
    if page.category and page.category in {c["name"] for c in catalog.categories()}:
        ctx.category = page.category
    product_id = page.product_id or (parts[1] if len(parts) == 2 and parts[0] == "products" else None)
    if product_id:
        product = catalog.get_product(product_id)
        if product:  # silently ignore ids that don't exist
            ctx.kind = "product"
            ctx.product_id = product["product_id"]
            ctx.product_name = product["name"]
            ctx.product_category = product["category"]
            ctx.product_garment_type = product["garment_type"]
            ctx.product_colors = product["colors"]
            ctx.product_price_usd = product["price"]
    return ctx


def to_message_history(history: list[ChatTurn]) -> list[ModelMessage]:
    """Turn the widget's plain-text transcript into Pydantic AI messages."""
    messages: list[ModelMessage] = []
    for turn in history[-MAX_HISTORY_TURNS:]:
        if turn.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=turn.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=turn.content)]))
    return messages


# ---------- loop limits + audit trail (Problem 12) ----------
MAX_MODEL_REQUESTS = 6  # model round-trips per shopper message (each tool step is one)
MAX_TOOL_CALLS = 8  # tool executions per shopper message
LIMITS = UsageLimits(request_limit=MAX_MODEL_REQUESTS, tool_calls_limit=MAX_TOOL_CALLS)


def _begin(channel: str, message: str, history: list[ChatTurn], deps: ShopDeps) -> float:
    audit.start_run()
    page = deps.page
    audit.record(
        "run_start",
        channel=channel,
        model=MODEL_NAME,
        shopper=f"user:{deps.customer.user_id}" if deps.customer else "guest",
        page=page.path if page else None,
        viewing=page.product_id if page else None,
        message=audit.short(message),
        history_turns=len(history),
    )
    return time.perf_counter()


def _stop_reason(e: Exception) -> str:
    if isinstance(e, UsageLimitExceeded):
        return "loop_limit"
    if isinstance(e, ModelHTTPError) and "content_filter" in str(e.body):
        return "content_filter"
    return "error"


def _end(t0: float, stop_reason: str, usage=None, messages=None, output: AgentOutput | None = None, error: str | None = None) -> None:
    finish = None
    for m in reversed(messages or []):
        if isinstance(m, ModelResponse):
            finish = m.finish_reason
            break
    audit.record(
        "run_end",
        stop_reason=stop_reason,
        model_finish_reason=finish,
        requests=getattr(usage, "requests", None),
        tool_calls=getattr(usage, "tool_calls", None),
        input_tokens=getattr(usage, "input_tokens", None),
        output_tokens=getattr(usage, "output_tokens", None),
        cards=len(output.product_ids) if output else 0,
        reply=audit.short(output.reply) if output else None,
        error=error,
        ms=round((time.perf_counter() - t0) * 1000),
    )


async def run_agent(message: str, history: list[ChatTurn], deps: ShopDeps) -> AgentOutput:
    t0 = _begin("chat", message, history, deps)
    try:
        result = await get_agent().run(message, message_history=to_message_history(history), deps=deps, usage_limits=LIMITS)
    except Exception as e:
        _end(t0, _stop_reason(e), error=audit.short(repr(e)))
        raise
    # the agent finished by returning its structured AgentOutput (the "final_result" output tool)
    _end(t0, "final_result", result.usage, result.all_messages(), result.output)
    return result.output


# ---------- streaming (Problem 9, B2) ----------

def _status_for(tool_name: str, args: dict) -> str | None:
    """Friendly progress text for the chat widget while a tool runs."""
    if tool_name == "search_products":
        what = args.get("query") or args.get("category") or "the catalogue"
        extras = []
        if args.get("size"):
            extras.append(f"in size {args['size']}")
        if args.get("max_price"):
            extras.append(f"under ${args['max_price']:g}")
        return f"Searching {what}{' ' + ' '.join(extras) if extras else ''}…"
    if tool_name in ("check_stock", "get_product_details"):
        product = catalog.get_product(str(args.get("product_id", "")))
        name = product["name"] if product else "that item"
        if tool_name == "check_stock":
            return f"Checking {args.get('size', '')} stock for {name}…".replace("  ", " ")
        return f"Looking up {name}…"
    if tool_name == "list_categories":
        return "Browsing our categories…"
    if tool_name == "get_shopper_context":
        return "Checking your account…"
    return None  # final_result etc.


async def stream_agent(message: str, history: list[ChatTurn], deps: ShopDeps):
    """Yield ("status", text), ("reply", partial_reply) and finally ("done", AgentOutput)."""
    agent = get_agent()
    t0 = _begin("chat_stream", message, history, deps)
    yield "status", "Thinking…"
    last_reply = ""
    try:
        async with agent.iter(message, message_history=to_message_history(history), deps=deps, usage_limits=LIMITS) as run:
            async for node in run:
                if Agent.is_model_request_node(node):
                    async with node.stream(run.ctx) as stream:
                        async for partial in stream.stream_output(debounce_by=0.03):
                            reply = getattr(partial, "reply", None) or ""
                            if reply and reply != last_reply:
                                last_reply = reply
                                yield "reply", reply
                elif Agent.is_call_tools_node(node):
                    for part in node.model_response.parts:
                        if getattr(part, "part_kind", "") != "tool-call":
                            continue
                        status = _status_for(part.tool_name, part.args_as_dict())
                        if status:
                            yield "status", status
    except Exception as e:
        _end(t0, _stop_reason(e), error=audit.short(repr(e)))
        raise
    _end(t0, "final_result", run.usage, run.result.all_messages(), run.result.output)
    yield "done", run.result.output
