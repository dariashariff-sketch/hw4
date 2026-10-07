"""Campus Customs accounts: password hashing, sessions, and /api/auth routes.

Passwords are never stored. We store a salted PBKDF2-SHA256 hash:
    pbkdf2_sha256$<iterations>$<salt>$<hex digest>   (new accounts)
    pbkdf2_sha256$<salt>$<hex digest>                (seeded users, 120,000 iterations)

Logged-in shoppers get a random session token in an HttpOnly cookie; the DB
only keeps a SHA-256 of that token, so a leaked DB can't be used to log in.
"""

import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel, Field

import catalog

DB_PATH = catalog.DB_PATH  # same data pack as the catalogue

ALGO = "pbkdf2_sha256"
ITERATIONS = 600_000  # OWASP 2023+ guidance for PBKDF2-SHA256
LEGACY_ITERATIONS = 120_000  # what the seeded users in the DB were hashed with
MIN_PASSWORD = 8
SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
MAX_FAILED = 5  # failed logins per email before a short lockout
LOCKOUT_SECONDS = 300
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

router = APIRouter(prefix="/api/auth", tags=["auth"])
_failed: dict[str, list[float]] = {}  # email -> recent failure timestamps (in memory)


# ---------- password hashing ----------

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), ITERATIONS).hex()
    return f"{ALGO}${ITERATIONS}${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if len(parts) == 4:
        algo, iterations, salt, digest = parts
        iterations = int(iterations)
    elif len(parts) == 3:
        algo, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    if algo != ALGO:
        return False
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()
    return hmac.compare_digest(candidate, digest)  # constant-time comparison


# A fixed hash used to spend the same time on unknown emails, so response
# timing doesn't reveal which emails have accounts.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# ---------- database ----------

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_sessions_table() -> None:
    with connect() as conn:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS sessions (
                token_hash TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )"""
        )
        conn.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _public_user(row: sqlite3.Row) -> dict:
    # Never include password_hash in anything that leaves the backend.
    first = row["first_name"] or row["name"].split(" ")[0]
    return {
        "id": row["id"],
        "first_name": first,
        "last_name": row["last_name"] or "",
        "email": row["email"],
        "member_since": (row["created_at"] or "")[:10],
    }


def user_from_token(token: str | None) -> dict | None:
    if not token:
        return None
    with connect() as conn:
        row = conn.execute(
            """SELECT u.* FROM sessions s JOIN users u ON u.id = s.user_id
               WHERE s.token_hash = ? AND s.expires_at > datetime('now')""",
            (_token_hash(token),),
        ).fetchone()
    return _public_user(row) if row else None


def _start_session(response: Response, user_id: int) -> None:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
            (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
        )
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=SESSION_DAYS * 86400,
        httponly=True,  # JavaScript can't read it, which blunts XSS token theft
        samesite="lax",
        secure=False,  # set True when served over HTTPS in production
        path="/",
    )


# ---------- routes ----------

class SignupIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=60)
    last_name: str = Field(min_length=1, max_length=60)
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)
    confirm_password: str = Field(max_length=128)


class LoginIn(BaseModel):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


@router.post("/signup")
def signup(body: SignupIn, response: Response) -> dict:
    first, last = body.first_name.strip(), body.last_name.strip()
    email = body.email.strip().lower()
    if not first or not last:
        raise HTTPException(400, "Please enter your first and last name.")
    if not EMAIL_RE.match(email):
        raise HTTPException(400, "Please enter a valid email address.")
    if len(body.password) < MIN_PASSWORD:
        raise HTTPException(400, f"Password must be at least {MIN_PASSWORD} characters.")
    if body.password != body.confirm_password:
        raise HTTPException(400, "Passwords don't match.")

    with connect() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with that email already exists. Try logging in.")
        cur = conn.execute(
            """INSERT INTO users (name, email, password_hash, first_name, last_name)
               VALUES (?, ?, ?, ?, ?)""",
            (f"{first} {last}", email, hash_password(body.password), first, last),
        )
        user_id = cur.lastrowid
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    _start_session(response, user_id)
    return {"user": _public_user(row)}


@router.post("/login")
def login(body: LoginIn, response: Response) -> dict:
    email = body.email.strip().lower()
    now = time.time()
    recent = [t for t in _failed.get(email, []) if now - t < LOCKOUT_SECONDS]
    if len(recent) >= MAX_FAILED:
        raise HTTPException(429, "Too many attempts. Please wait a few minutes and try again.")

    with connect() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
    ok = verify_password(body.password, row["password_hash"] if row else _DUMMY_HASH)
    if not row or not ok:
        _failed[email] = recent + [now]
        # Same message either way so attackers can't probe which emails exist.
        raise HTTPException(401, "Incorrect email or password.")

    _failed.pop(email, None)
    _start_session(response, row["id"])
    return {"user": _public_user(row)}


@router.post("/logout")
def logout(response: Response, cc_session: str | None = Cookie(default=None)) -> dict:
    if cc_session:
        with connect() as conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(cc_session),))
    response.delete_cookie(SESSION_COOKIE, path="/")
    return {"ok": True}


@router.get("/me")
def me(cc_session: str | None = Cookie(default=None)) -> dict:
    return {"user": user_from_token(cc_session)}
