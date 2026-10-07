# Campus Customs: Shop + AI Shopping Assistant (MGT 409, Homework 4)

Created a fun customer website for Campus Customs, the oldest official Yale merchandise shop.

A customer website for **Campus Customs**, a Yale merch shop at 57 Broadway, New Haven, with a shopping assistant built on **Pydantic AI**. Shoppers can:
- browse products and open single-item pages
- create an account and log in
- chat about the merch they want, and watch matching items appear on the page as cards
- get honest price and stock answers, read live from a local SQLite database

The home page is an interactive, illustrated Yale dorm room: click the hoodie on the chair to step into the shop.

- **Frontend:** React + Vite + TypeScript (`frontend/`)
- **Backend:** Python FastAPI (`backend/main.py`)
- **Agent:** Pydantic AI using `gpt-5.6-luna` through the Portkey gateway

## The agent: 4 files in `backend/`

| File | Role |
|---|---|
| `backend/prompts/prompt.md` | System prompt: Campus Customs voice, "only use tool data" rules, how to show products on the page, customer memory and page context, safety rules |
| `backend/agent.py` | Agent wiring: model + Portkey, the prompt, tools, dynamic customer/page instructions, loop limits, streaming, audit hooks |
| `backend/tools.py` | The agent's 5 read-only tools: `search_products`, `get_product_details`, `check_stock`, `list_categories`, `get_shopper_context` |
| `backend/models.py` | Pydantic types: chat request/reply, product cards, tool results, agent output, agent deps |

Supporting backend modules:
- `main.py`: API routes
- `catalog.py`: read-only database access
- `search.py`: smarter search
- `auth.py`: accounts and sessions
- `memory.py`: saved chats
- `safety.py`: crisis guard
- `audit.py`: append-only audit trail
- `clean_images.py`: photo cleanup

## What is not in this repo

The **data pack** and **secrets** are kept out on purpose (see `.gitignore`):
- `campus_customs.db`: the SQLite database (catalogue, inventory, users, chats)
- `products/*.jpg`: the product photos
- `.env`: your real API key. Copy `.env.example` to create it.

## Setup

**Requirements:** Python 3.12+ and Node.js 20+.

### 1. Place the data pack
Put the course data pack inside `hw4/` so it looks like this:
```
hw4/
  data/
    campus_customs.db
    products/            (the 102 product .jpg files)
  backend/  frontend/  ...
```
If you unzip `data.zip`, its `data/` folder goes straight into `hw4/`. A `data/` folder next to `hw4/` also works, or you can point to any location with `CC_DATA_DIR` in `.env`.

### 2. Add your API key
```
cp .env.example .env        # Windows PowerShell: copy .env.example .env
```
Then edit `.env` and set `PORTKEY_API_KEY=` to your Portkey key.

### 3. Install
```
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt     # macOS/Linux: .venv/bin/python -m pip ...
cd frontend
npm install
cd ..
```
Optional: make the white-background product photos used by the site's design:
```
cd backend
../.venv/Scripts/python clean_images.py      # writes data/products_clean/ (also kept out of git)
cd ..
```
Without this step the site still works, and shows the original photos.

## Run it (two terminals)

**Terminal 1: backend** (run from `backend/`, with the venv active):
```
cd backend
source ../.venv/Scripts/activate      # PowerShell: ..\.venv\Scripts\Activate.ps1   macOS/Linux: source ../.venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Terminal 2: frontend:**
```
cd frontend
npm run dev
```
Open **http://localhost:5173**. The Vite dev server forwards `/api` and `/media` to the backend on port 8000.

Test login: `test@campuscustoms.yale.edu` / `password` (or create a new account on the site).

## Things to try
- On the home page, click the **hoodie on the chair** (or any glowing object) to zoom into that part of the shop.
- Open the chat ("Chat with us") and ask *"What quarter-zips do you have?"*. Matching cards slide onto the page.
- On a product page, ask *"Is this in stock in L?"* or *"do you have this in rainbow?"*. The agent knows which product you're viewing.
- Log in, chat, log out, and log back in: your conversation is remembered.

## Docs and checks (`output/`)
- `harness.md`: the full system spec (architecture, how to run, model fields and why, tools, safety rules, limits, audit format) plus the build history
- `app_check.html`: the live-site test, with screenshots (open it by double-clicking). Re-run it with `.venv/Scripts/python tests/app_check.py` while both servers are running (needs `pip install playwright` and Microsoft Edge).
- `audit_trail.json`: an append-only log of agent-loop activity (time, tool, short args and result, stop reason)
- `usability.md`, `design.md`: usability and visual-design notes
- `AI_prompts.md`: the log of prompts used to build this project
