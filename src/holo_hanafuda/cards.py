from dataclasses import dataclass
from typing import List, Dict

@dataclass(frozen=True, order=True)
class Card:
    month: int  # 1..12
    kind: str   # "bright","animal","ribbon","kasu"
    tag: str = ""  # e.g. "rain","sake","boar","deer","butterfly","geese","swallow","moon","cherry","poetry-red","blue","plain"

    def key(self) -> str:
        return f"{self.month}:{self.kind}{('-'+self.tag) if self.tag else ''}"

# Build standard Hanafuda 48-card set (simplified tags)
def _build_cards() -> List[Card]:
    C: List[Card] = []

    # Brights (1,3,8,11,12)
    C += [
        Card(1,  "bright", "crane"),
        Card(3,  "bright", "cherry"),
        Card(8,  "bright", "moon"),
        Card(11, "bright", "rain"),
        Card(12, "bright", "phoenix"),
    ]

    # Animals（※11月=swallow を追加）
    C += [
        Card(2,  "animal", "nightingale"),
        Card(4,  "animal", "cuckoo"),
        Card(5,  "animal", "bridge"),
        Card(6,  "animal", "butterfly"),
        Card(7,  "animal", "boar"),
        Card(8,  "animal", "geese"),
        Card(9,  "animal", "sake"),
        Card(10, "animal", "deer"),
        Card(11, "animal", "swallow"),
    ]

    # Ribbons (1枚/各月)
    red_poetry = {1, 2, 3}
    blue = {6, 9, 10}
    for m in range(1, 13):
        if m in red_poetry:
            C.append(Card(m, "ribbon", "poetry-red"))
        elif m in blue:
            C.append(Card(m, "ribbon", "blue"))
        else:
            C.append(Card(m, "ribbon", "plain"))

    # 各月4枚に満たない分をカスで埋める
    from collections import defaultdict
    count = defaultdict(int)
    for c in C:
        count[c.month] += 1
    for m in range(1, 13):
        remaining = 4 - count[m]
        for _ in range(remaining):
            C.append(Card(m, "kasu", ""))

    assert len(C) == 48, f"Deck size mismatch: {len(C)}"
    return sorted(C)

ALL_CARDS: List[Card] = _build_cards()
CARD_INDEX = {c.key(): c for c in ALL_CARDS}

def parse_card(token: str) -> Card:
    """Parse '<month>:<kind[-tag]>' into Card (for external JSON)."""
    token = token.strip()
    if token in CARD_INDEX:
        return CARD_INDEX[token]
    if ":" not in token:
        raise ValueError(f"Invalid card token: {token}")
    m_str, rest = token.split(":", 1)
    m = int(m_str)
    if "-" in rest:
        kind, tag = rest.split("-", 1)
    else:
        kind, tag = rest, ""
    kind = kind.lower()
    tag = tag.lower()

    # synonyms
    syn = {
        "bright": "bright", "hikari": "bright",
        "animal": "animal", "tane": "animal",
        "ribbon": "ribbon", "tan": "ribbon",
        "kasu": "kasu"
    }
    kind = syn.get(kind, kind)

    tag_syn = {
        "rain": "rain", "sake": "sake", "moon": "moon", "cherry": "cherry",
        "boar": "boar", "deer": "deer", "butterfly": "butterfly",
        "geese": "geese", "swallow": "swallow",
        "red": "poetry-red", "poetry": "poetry-red",
        "blue": "blue", "plain": "plain"
    }
    tag = tag_syn.get(tag, tag)

    candidates = [c for c in ALL_CARDS if c.month == m and c.kind == kind and (tag == "" or c.tag == tag)]
    if not candidates:
        candidates = [c for c in ALL_CARDS if c.month == m and c.kind == kind]
    if not candidates:
        raise KeyError(f"Unknown card: {token}")
    return candidates[0]
