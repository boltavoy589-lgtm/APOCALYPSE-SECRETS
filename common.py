import re


def split_sentences(script):
    """Split a script into scenes (one per sentence). Used by every step so scene numbers match."""
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", script) if s.strip()]
