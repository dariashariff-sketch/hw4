"""Problem 11: live-site app check.

Drives the running site (frontend :5173 + backend :8000) in a real browser (installed
Microsoft Edge via Playwright), takes the screenshots for output/app_check.html, and
records what the chat actually said next to the database's ground truth.

Run from the homework 4 folder (both servers must be running):
    .venv/Scripts/python tests/app_check.py
"""

import json
import sqlite3
import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "app_check_images"
sys.path.insert(0, str(ROOT / "backend"))
from catalog import DB_PATH as DB  # noqa: E402  (same data-pack lookup as the backend)
SITE = "http://localhost:5173"
VIEWPORT = {"width": 1440, "height": 900}


def ask(page: Page, question: str) -> str:
    """Type a question into the chat widget and wait for the streamed answer to finish."""
    before = page.locator(".msg-assistant .bubble").count()
    page.fill(".chat-input input", question)
    page.press(".chat-input input", "Enter")
    page.wait_for_function(
        "n => document.querySelectorAll('.msg-assistant .bubble').length > n"
        " && !document.querySelector('.is-streaming') && !document.querySelector('.status-bubble')",
        arg=before,
        timeout=60_000,
    )
    page.wait_for_timeout(900)  # let the results shelf animation land
    return page.locator(".msg-assistant .bubble").last.inner_text()


def open_chat(page: Page) -> None:
    page.click(".chat-fab")
    page.wait_for_selector(".chat-input input")


def db_truth() -> dict:
    con = sqlite3.connect(f"file:{DB.as_posix()}?mode=ro", uri=True)
    price = con.execute("SELECT price FROM catalogue WHERE product_id = 'berkeley-1-4-zip'").fetchone()[0]
    stock = dict(con.execute("SELECT size, quantity FROM inventory WHERE product_id = 'berkeley-1-4-zip'").fetchall())
    qz = [r[0] for r in con.execute("SELECT product_id FROM catalogue ORDER BY product_id")]
    return {"price": price, "stock": stock, "all_ids": qz}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    truth = db_truth()
    results: dict = {"db": {"berkeley_price": truth["price"], "berkeley_stock": truth["stock"]}}

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)

        # ---------- Check 1: chat answers an inventory question from the DB ----------
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
        page = ctx.new_page()
        page.goto(f"{SITE}/products/berkeley-1-4-zip")
        page.wait_for_selector(".pdp h1")
        open_chat(page)
        q1 = "How many of these do you have left in size L, and what is the price?"
        a1 = ask(page, q1)
        # clear the results shelf so the product page (price + stock table) sits beside the chat
        if page.locator(".shelf-btn", has_text="Clear").count():
            page.click(".shelf-btn >> text=Clear")
        page.wait_for_timeout(300)
        page.locator(".stock-table").scroll_into_view_if_needed()
        page.evaluate("window.scrollBy(0, -220)")
        page.wait_for_timeout(500)
        page.screenshot(path=OUT / "inventory.png")
        results["check1"] = {"question": q1, "answer": a1}
        ctx.close()

        # ---------- Check 2: category question -> dynamic product cards on the page ----------
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
        page = ctx.new_page()
        page.goto(f"{SITE}/")
        page.wait_for_selector(".dorm")
        open_chat(page)
        q2 = "What quarter-zips do you have?"
        a2 = ask(page, q2)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1200)
        page.screenshot(path=OUT / "quarterzip_cards.png")
        cards = page.locator(".shelf .card h3").all_inner_texts()
        results["check2"] = {
            "question": q2,
            "answer": a2,
            "shelf_title": page.locator(".shelf h2").inner_text().split("\n")[0],
            "cards": cards,
        }

        # ---------- Check 3 (Problem 9, F1): quick add from a card + mini-cart drawer ----------
        page.click(".chat-head button[aria-label='Close chat']")
        card = page.locator(".shelf-card").nth(1)
        name = card.locator("h3").inner_text()
        card.locator(".quick-size:not([disabled])", has_text="M").first.click()
        card.locator(".quick-btn").click()
        page.wait_for_selector(".mini-cart.open")
        page.wait_for_timeout(600)
        page.screenshot(path=OUT / "usability_quick_add.png")
        results["check3"] = {
            "product": name,
            "drawer_text": page.locator(".mini-added").inner_text(),
            "subtotal": page.locator(".mini-foot .sum-row").inner_text(),
            "url_after_add": page.url,
        }
        ctx.close()

        # ---------- Check 4 (Problem 10): the 2.5D dorm-room home page ----------
        # motion on, like a normal desktop browser (the room turns its effects off for "reduce motion")
        ctx = browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5, reduced_motion="no-preference")
        page = ctx.new_page()
        page.goto(f"{SITE}/")
        page.wait_for_selector(".dorm .hs-hoodie")
        page.wait_for_timeout(1500)
        page.mouse.move(1180, 300)  # nudge the parallax and hover the pennant so its glow + label show
        page.hover(".hs-pennant .hs-art")
        page.wait_for_timeout(700)
        page.screenshot(path=OUT / "dorm_room.png")
        results["check4"] = {
            "clickable_objects": page.locator(".dorm .hs").count(),
            "depth_layers": page.locator(".dorm .layer").count(),
            "layer_offsets": page.evaluate("[...document.querySelectorAll('.dorm .layer')].map(l => l.style.transform)"),
        }
        ctx.close()
        browser.close()

    (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
