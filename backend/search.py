"""Smarter catalogue search (Problem 9, B1).

The old search required every query word to appear verbatim, so "grandpa gift",
"quarterzip", "hoody" and "handsome dan" all returned nothing. This version:
  1. normalizes words (lowercase, strips punctuation, simple plurals),
  2. drops filler words ("gift", "for", "my", "something"...),
  3. expands synonyms (hoody -> hoodie, quarterzip -> quarter-zip, grandparent -> grandpa/grandma...),
  4. tolerates small typos (fuzzy match against the catalogue's own vocabulary),
  5. ranks by relevance (name > tags > category/colors > description) instead of A-Z,
  6. reports words it couldn't match ("rainbow"), so the agent can be honest about them.
"""

import difflib
import re
from dataclasses import dataclass, field

FILLER = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with", "my", "me", "i", "im", "i'm",
    "you", "your", "do", "does", "have", "has", "any", "some", "something", "anything", "stuff", "show",
    "want", "looking", "look", "find", "get", "need", "please", "pls", "u", "ur", "got", "sell", "carry",
    "item", "items", "thing", "things", "gift", "gifts", "present", "idea", "ideas", "cool", "nice",
    "good", "great", "cute", "what", "which", "that", "this", "it", "is", "are", "there", "options",
    "option", "piece", "pieces", "merch", "gear", "apparel", "clothing", "clothes", "one", "ones",
}

# each key expands to any of its alternatives; a product matches the word if it matches any of them
SYNONYMS = {
    "hoodie": ["hoodie", "hood", "hooded"],
    "hoody": ["hoodie", "hood", "hooded"],
    "hoodies": ["hoodie", "hood", "hooded"],
    "sweatshirt": ["sweatshirt", "hoodie", "crewneck", "crew"],
    "jumper": ["sweatshirt", "crewneck", "hoodie"],
    "sweater": ["sweater", "crewneck", "fleece", "sweatshirt"],
    "crewneck": ["crewneck", "crew neck", "crew"],
    "crew": ["crewneck", "crew neck", "crew"],
    "quarterzip": ["quarter-zip", "quarter zip", "1/4 zip"],
    "quarter": ["quarter-zip", "quarter zip", "1/4 zip"],
    "qz": ["quarter-zip", "quarter zip", "1/4 zip"],
    "pullover": ["pullover"],
    "zip": ["zip"],
    "tee": ["t-shirt", "tee"],
    "tshirt": ["t-shirt", "tee"],
    "shirt": ["shirt", "tee", "t-shirt"],
    "jacket": ["jacket", "fleece", "bomber"],
    "coat": ["jacket", "fleece"],
    "fleece": ["fleece", "sherpa"],
    "longsleeve": ["long sleeve", "long-sleeve"],
    "grey": ["gray", "grey", "charcoal"],
    "gray": ["gray", "grey", "charcoal"],
    "blue": ["blue", "navy"],
    "navy": ["navy"],
    "maroon": ["maroon", "red", "crimson"],
    "handsome": ["bulldog"],
    "dan": ["bulldog"],
    "dog": ["bulldog"],
    "puppy": ["bulldog"],
    "mascot": ["bulldog"],
    "bulldog": ["bulldog"],
    "grandparent": ["grandpa", "grandma"],
    "grandfather": ["grandpa"],
    "granddad": ["grandpa"],
    "grandma": ["grandma"],
    "grandmother": ["grandma"],
    "granny": ["grandma"],
    "mother": ["mom"],
    "mum": ["mom"],
    "mama": ["mom"],
    "father": ["dad"],
    "papa": ["dad"],
    "parent": ["mom", "dad"],
    "sibling": ["brother", "sister"],
    "bro": ["brother"],
    "sis": ["sister"],
    "harvard": ["harvard", "the game"],
    "game": ["the game", "game"],
    "football": ["football"],
    "hockey": ["hockey"],
    "workout": ["performance", "dry zone", "tech", "sports"],
    "gym": ["performance", "dry zone", "tech", "sports"],
    "athletic": ["performance", "sports", "tech"],
    "vintage": ["vintage", "retro"],
    "retro": ["vintage", "retro"],
    "som": ["school of management"],
    "law": ["law school", "law"],
}

# where a hit counts most: a match in the product name is a stronger signal than one in the description
FIELD_WEIGHTS = (("name", 5), ("tags", 3), ("category", 3), ("colors", 3), ("description", 1))


@dataclass
class SearchOutcome:
    products: list[dict]
    ignored_terms: list[str] = field(default_factory=list)  # words that matched nothing in the catalogue
    used_terms: list[str] = field(default_factory=list)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9/\- ]+", " ", text.lower().replace("’", "'")).strip()


def _singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def _fields(p: dict) -> dict[str, str]:
    return {
        "name": _norm(p["name"] + " " + p["raw_name"]),
        "tags": _norm(" ".join(p["search_tags"])),
        "category": _norm(p["category"] + " " + p["garment_type"]),
        "colors": _norm(" ".join(p["colors"])),
        "description": _norm(p["description"]),
    }


def _tokens(q: str) -> list[str]:
    q = _norm(q)
    # glue common multi-word forms before splitting
    for a, b in (("quarter zip", "quarterzip"), ("1/4 zip", "quarterzip"), ("t shirt", "tshirt"),
                 ("t-shirt", "tshirt"), ("long sleeve", "longsleeve"), ("long-sleeve", "longsleeve"),
                 ("crew neck", "crewneck"), ("handsome dan", "handsome"), ("quarter-zip", "quarterzip")):
        q = q.replace(a, b)
    words = [w.strip("-/") for w in q.split()]
    return [w for w in words if w and w not in FILLER]


def _alternatives(word: str, vocab: set[str]) -> list[str]:
    for key in (word, _singular(word)):
        if key in SYNONYMS:
            return SYNONYMS[key]
    base = _singular(word)
    alts = [base] if base == word else [word, base]
    if not any(a in vocab for a in alts) and len(base) >= 4:
        # small typos: "hodie", "crewnek", "quater"
        alts += difflib.get_close_matches(base, list(vocab), n=2, cutoff=0.8)
    return alts


def _hit(alt: str, text: str) -> bool:
    return re.search(r"(?<![a-z0-9])" + re.escape(alt), text) is not None


def ranked_search(query: str, products: list[dict]) -> SearchOutcome:
    words = _tokens(query)
    if not words:
        return SearchOutcome(products=products)

    indexed = [(p, _fields(p)) for p in products]
    vocab = {w for _, f in indexed for text in f.values() for w in text.split()}

    terms: list[tuple[str, list[str]]] = []
    ignored: list[str] = []
    for w in words:
        alts = _alternatives(w, vocab)
        if any(_hit(a, text) for _, f in indexed for text in f.values() for a in alts):
            terms.append((w, alts))
        else:
            ignored.append(w)  # e.g. "rainbow": nothing in the catalogue mentions it

    if not terms:
        return SearchOutcome(products=[], ignored_terms=ignored)

    scored = []
    for p, f in indexed:
        matched, score = 0, 0
        for _, alts in terms:
            best = max((weight for name, weight in FIELD_WEIGHTS if any(_hit(a, f[name]) for a in alts)), default=0)
            if best:
                matched += 1
                score += best
        if matched:
            scored.append((matched, score, p))

    # Require every searchable word to match when possible; otherwise fall back to the best partial matches.
    full = [s for s in scored if s[0] == len(terms)]
    pool = full or [s for s in scored if s[0] >= max(1, (len(terms) + 1) // 2)]
    pool.sort(key=lambda s: (-s[0], -s[1], s[2]["name"]))
    return SearchOutcome(products=[s[2] for s in pool], ignored_terms=ignored, used_terms=[t for t, _ in terms])
