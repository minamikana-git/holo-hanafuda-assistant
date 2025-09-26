from dataclasses import dataclass
from typing import List, Tuple, Dict

@dataclass(frozen=True, order=True)
class Card:
    month: int  # 1..12
    kind: str   # "bright","animal","ribbon","ribbon-red","ribbon-blue","kasu","special"

    tag: str = ""  # e.g., "rain","sake","boar","deer","butterfly","moon","cherry","poetry-red","poetry-blue"

    def key(self) -> str:
        return f"{self.month}:{self.kind}{('-'+self.tag) if self.tag else ''}"

# Build standard Hanafuda 48-card set (simplified tags)
def _build_cards() -> List[Card]:
    C: List[Card] = []
    # Month mapping: 1 Matsu,2 Ume,3 Sakura,4 Fuji,5 Ayame,6 Botan,7 Hagi,8 Susuki,9 Kiku,10 Momiji,11 Yanagi,12 Kiri
    # Brights
    C += [Card(1,"bright","crane"), Card(3,"bright","cherry"), Card(8,"bright","moon"),
          Card(11,"bright","rain"), Card(12,"bright","phoenix")]
    # Animals
    C += [Card(2,"animal","nightingale"), Card(4,"animal","cuckoo"), Card(5,"animal","bridge"),
          Card(6,"animal","butterfly"), Card(7,"animal","boar"), Card(8,"animal","geese"),
          Card(9,"animal","sake"), Card(10,"animal","deer")]
    # Ribbons (red/blue/poetry simplified)
    red_poetry = {1,2,3}
    blue = {6,9,10}
    for m in range(1,13):
        if m in red_poetry:
            C.append(Card(m,"ribbon","poetry-red"))
        elif m in blue:
            C.append(Card(m,"ribbon","blue"))
        else:
            C.append(Card(m,"ribbon","plain"))

    # --- FIX: fill each month up to 4 cards with kasu ---
    from collections import defaultdict
    count = defaultdict(int)
    for c in C:
        count[c.month] += 1
    for m in range(1,13):
        remaining = 4 - count[m]
        for _ in range(remaining):
            C.append(Card(m, "kasu", ""))

    assert len(C) == 48, f"Deck size mismatch: {len(C)}"
    return sorted(C)


def parse_card(token: str) -> Card:
    """Parse '<month>:<kind[-tag]>' into Card (for external JSON)."""
    token = token.strip()
    if token in CARD_INDEX:
        return CARD_INDEX[token]
    # try normalizations
    if ":" not in token:
        raise ValueError(f"Invalid card token: {token}")
    m_str, rest = token.split(":",1)
    m = int(m_str)
    if "-" in rest:
        kind, tag = rest.split("-",1)
    else:
        kind, tag = rest, ""
    kind = kind.lower()
    tag = tag.lower()
    # map common synonyms
    syn = {"bright":"bright", "hikari":"bright", "animal":"animal", "tane":"animal",
           "ribbon":"ribbon", "tan":"ribbon", "kasu":"kasu"}
    kind = syn.get(kind, kind)
    # canonicalize known tags
    tag_syn = {
        "rain":"rain", "sake":"sake", "moon":"moon","cherry":"cherry",
        "boar":"boar","deer":"deer","butterfly":"butterfly",
        "red":"poetry-red","blue":"blue","plain":"plain","poetry":"poetry-red"
    }
    tag = tag_syn.get(tag, tag)
    # Try to locate matching card
    candidates = [c for c in ALL_CARDS if c.month==m and c.kind==kind and (tag=="" or c.tag==tag)]
    if not candidates:
        # fallback: ignore tag
        candidates = [c for c in ALL_CARDS if c.month==m and c.kind==kind]
    if not candidates:
        raise KeyError(f"Unknown card: {token}")
    # If multiple, pick the first
    return candidates[0]
