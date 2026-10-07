# Campus Customs: Usability Improvements (Problem 9)

We brainstormed 4 frontend and 4 backend ideas. Those that weren't picked are listed at the end. We built **3 frontend** improvements (F1, F2, F3) and **2 backend** improvements (B1, B2). For each one: what we added, and why it helps the shopper or the CC business.

---

## Frontend

### F1. Add to cart straight from product cards, plus a mini-cart drawer
**What we added**
- **Quick add on every card.** This covers the chat results shelf *and* the Products page grid. Each card has a row of size buttons (XS–XXL) and an **"Add M to cart"** button. Sold-out sizes are crossed out and can't be picked, and hovering a size shows its live stock ("Only 2 left"). A product that's sold out everywhere says so instead of showing buttons.
- **Mini-cart drawer.** After any add, from a card *or* the product page, a drawer slides in from the right. It shows "✓ Added to your cart" with the item, size and price, every line in the cart, the subtotal, and two big buttons: **Checkout** and **Keep shopping**. It closes with ✕, Escape, a click outside it, or a page change.
- Files: `components/QuickAdd.tsx`, `components/MiniCart.tsx`, and `cart.tsx` (new `lastAdded` / `drawerOpen` state).

**Why it helps**
- **Shopper:** buying from the chat used to take five steps (shelf → product page → pick size → Add to Cart → find the cart). Now it's **two clicks on the same screen**, pick a size and add, and they never lose their place in the results.
- **CC business:** fewer steps between "I like that" and "it's in my cart" means fewer abandoned sessions and more sales. The drawer makes the next step, **Checkout**, impossible to miss, which is the "never in doubt" goal from Problem 3. Showing the running subtotal also invites a second item.
- Quantities are capped at the database stock for that size, so shoppers can't add more than CC actually has.

### F2. Suggested-question chips in the chat
**What we added**
- A row of one-tap question chips above the chat input. **They change with where the shopper is** (`suggestionsFor()` in `ChatWidget.tsx`):

| Where the shopper is | Chips |
|---|---|
| Home / anywhere | "What hoodies do you have?", "Gifts under $40", "Anything with a bulldog?", "Quarter-zips in size M" |
| A product page | "Is this in stock in M?", "What colors does this come in?", "Show me similar items", "What's your return policy?" |
| A category page | "Crewnecks under $60", "Which crewnecks have XL in stock?", ... |
| After the chat put results on the page | "Which of these have M in stock?", "Anything cheaper?", "Show me hoodies instead", ... |

- Tapping a chip sends it right away. The chips hide while the assistant is answering.

**Why it helps**
- **Shopper:** many people don't know what a store chatbot can do, or don't want to type, especially on a phone. Chips show the kinds of questions that work (price, size, stock, gifts) and turn them into a single tap. On a product page, "Is this in stock in M?" works because of the page context from Problem 8.
- **CC business:** more shoppers actually use the assistant. The chips lead them toward questions that end in product cards and a cart, and the follow-up chips keep the conversation going instead of ending after one answer.

### F3. Live progress and formatted replies in the chat
**What we added**
- **Progress text instead of a silent wait:** while the assistant works, its bubble shows what it's doing, using live events from B2:
  "Thinking…" → "Searching quarter-zips in size M…" → "Checking M stock for Branford Quarter-Zip…" → "Looking up Berkeley Quarter-Zip…".
- **The reply streams in** as it's written, with a blinking cursor (▍), instead of appearing all at once at the end.
- **Readable formatting:** `components/RichText.tsx` displays **bold** text and `- ` bullet lists properly. Before this, some replies (and older saved chats) showed raw `**asterisks**`. It builds normal React elements (no raw HTML), so a message can't inject code into the page.

**Why it helps**
- **Shopper:** a 5-second wait with only "…" feels broken. Seeing "Checking M stock for Branford Quarter-Zip…" makes it feel fast, and it also builds **trust**: the shopper can see the assistant is checking real stock, not guessing. That's CC's core promise.
- **CC business:** fewer people give up and close the chat while waiting, and well-formatted answers look professional and on-brand.

---

## Backend

### B1. Smarter catalogue search
**What we added** (`backend/search.py`, used by `catalog.search_products_ranked()`):
- **Normalizing:** lowercase, punctuation stripped, simple plurals ("hoodies" → "hoodie").
- **Filler words removed:** "gift", "for", "my", "something", "show me", ...
- **Synonyms:** hoody → hoodie; quarterzip / quarter zip / 1/4 zip → quarter-zip; tee / t shirt → T-shirt; grey ↔ gray; "handsome dan" / dog / mascot → bulldog; grandfather / grandparent → grandpa (and grandma); mother → mom; gym / workout → performance and sports items; and more.
- **Typo tolerance:** words are fuzzy-matched against the catalogue's own vocabulary ("hodie" → hoodie, "crewnek" → crewneck).
- **Relevance ranking** instead of A–Z. A match in the product *name* counts most, then tags, category and colors, then description. Results must match every searchable word when possible; otherwise the best partial matches are returned.
- **Honest leftovers:** words that match nothing in the catalogue come back as `ignored_terms` (e.g. "rainbow"). The prompt tells the agent to say plainly that we don't have them.
- It also powers the **Products page search box**, through the same function.

**Before → after** (number of products found):

| Search | Before | After |
|---|---|---|
| "grandpa gift" | 0 | 2: Yale Grandpa Crewneck, Yale Grandpa Hoodie |
| "something for my mom" | 0 | 2: Yale Mom Crewneck, Yale Mom Hoodie |
| "quarterzip" | 0 | the quarter-zips |
| "hoody" / "hodie" (typo) | 0 | all 27 hoodies |
| "handsome dan" | 0 | 10 bulldog items |
| "rainbow hoodie" | 0 | 27 hoodies + `ignored_terms: ["rainbow"]` → "we don't have rainbow, but here are our hoodies" |

**Why it helps**
- **Shopper:** people search in their own words, with typos and gift phrasing. Before, the assistant said "sorry, we don't have that" when CC actually *did* (it missed the Yale Grandpa hoodie in Problem 8). Now they find the right item on the first try.
- **CC business:** every false "we don't have it" is a lost sale. Better search turns those into product cards, and ranking puts the most relevant items first, where shoppers actually click. It also saves model calls, because the agent no longer has to retry searches with different wording.

### B2. Streaming replies (Server-Sent Events)
**What we added**
- A new endpoint, **`POST /api/chat/stream`**, that sends the answer **as it's being produced**, as `text/event-stream`:
  - `{"type": "status", "text": "Searching quarter-zips in size M…"}`, sent when the agent starts each tool call
  - `{"type": "reply", "text": "We've got 9 quarter-zips…"}`, the reply so far, growing as the model writes
  - `{"type": "done", "reply": ..., "results": ..., "saved": ...}`, the final answer with the product cards (same shape as `/api/chat`)
  - `{"type": "error", "detail": ...}`
- `agent.stream_agent()` uses Pydantic AI's `agent.iter()`. When a tool call is made, it turns it into friendly status text (`_status_for`). When the final answer is generated, it streams the partial structured output (`stream.stream_output()`), so the `reply` field arrives piece by piece.
- Everything else stays the same as the regular chat: customer memory is saved at the end, the provider's content filter gets the polite refusal, and product cards are still rebuilt from the database. `POST /api/chat` (non-streaming) still works as a fallback.
- The frontend reads the stream with `fetch()` and `ReadableStream` (`api.ts: streamChat`).

**Measured** (talking to the real server):

| Question | Before (one response at the end) | Now (streaming) |
|---|---|---|
| "Is the Berkeley quarter-zip available in medium?" | nothing for ~7.4 s | "Thinking…" at **0.4 s**, "Searching Berkeley quarter-zip…" at **3.5 s**, "Checking M stock…" at **5.5 s**, reply text at 7.3 s |
| "Quarter-zips in size M" (browser) | nothing for ~4.7 s | progress at **0.2 s** and **2.3 s**, reply streaming from **4.1 s** |
| "Is this in stock in M?" on the Branford page | n/a | "Checking M stock for Branford Quarter-Zip…" at **1.8 s**, done at 3.5 s ("20 available", which matches the DB) |

**Why it helps**
- **Shopper:** the chat responds within half a second instead of staying silent for several. People judge speed by when something first appears on screen, not when the answer is complete, so the same answer *feels* much faster. The live status also shows them what's being checked.
- **CC business:** a responsive assistant gets used more and abandoned less. It also gives CC visibility into what the agent does on each question (which tools it calls), which helps with debugging and future tuning.

---

## Ideas we didn't build (for later)
- **F4. Size guide + "Notify me when back in stock":** turns a sold-out size into a saved lead instead of a dead end.
- **B3. Speed and cost tuning:** cache the catalogue in memory, answer simple FAQs without calling the AI, and log the time each step takes.
- **B4. Cart actions from chat:** an `add_to_cart` tool so "add the Berkeley in medium to my cart" works, with stock checked first.
