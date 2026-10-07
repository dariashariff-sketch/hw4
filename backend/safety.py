"""Deterministic safety net that runs before the LLM (Problem 12).

The model provider's content filter can block crisis messages outright, and then the
agent never gets the chance to respond with care. So clear self-harm / danger phrases
are caught here first and always get the same supportive reply with help resources.
"""

import re

_CRISIS = re.compile(
    r"\b("
    r"kill(ing)? myself|suicid\w*|end(ing)? (it all|my life)|take my (own )?life|"
    r"(do ?n[o']?t|dont|no longer) want to (be alive|live|exist)|want to die|wanna die|"
    r"better off dead|hurt(ing)? myself|self[- ]?harm|cut(ting)? myself|overdose"
    r")\b",
    re.IGNORECASE,
)

CRISIS_REPLY = (
    "I'm really sorry you're feeling this way, and I'm glad you said something. You don't have to go "
    "through it alone. If you're in the U.S., you can call or text 988 to reach the Suicide & Crisis "
    "Lifeline any time, day or night. If you're in immediate danger, please call 911. Yale students can "
    "also reach Yale Mental Health & Counseling. I'm just a shopping assistant, but I hope you reach out "
    "to someone who can help right now."
)


def is_crisis(text: str) -> bool:
    return bool(_CRISIS.search(text or ""))
