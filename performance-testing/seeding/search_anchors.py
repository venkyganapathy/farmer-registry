"""Generates the fixed pool of search anchors and embeds them into names.

Each anchor is a random N-char lowercase string. Every seeded farmer's
first_name gets exactly one anchor spliced in at a random position (not just
prefixed), so a Locust user searching `%anchor%` exercises pg_trgm's
substring matching rather than only prefix matching.

Anchors are assigned to farmers round-robin (next_anchor). 10_000 anchors
on a 10M target gives ~1_000 farmers per term.
"""

import random
import string

from config import SEARCH_ANCHOR_COUNT, SEARCH_ANCHOR_LENGTH


def generate_anchors(count: int = SEARCH_ANCHOR_COUNT, length: int = SEARCH_ANCHOR_LENGTH) -> list[str]:
    anchors: set[str] = set()
    while len(anchors) < count:
        anchors.add("".join(random.choices(string.ascii_lowercase, k=length)))
    return sorted(anchors)


_round_robin_index = 0


def next_anchor(anchors: list[str]) -> str:
    global _round_robin_index
    anchor = anchors[_round_robin_index % len(anchors)]
    _round_robin_index += 1
    return anchor


def embed_anchor(base_name: str, anchor: str) -> str:
    position = random.randint(0, len(base_name))
    return base_name[:position] + anchor + base_name[position:]
