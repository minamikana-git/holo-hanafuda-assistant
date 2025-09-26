from typing import List, Tuple, Dict
from dataclasses import dataclass
from .cards import Card
from .koikoi_rules import yaku_points, list_yaku_progress

@dataclass
class Move:
    play: Card
    capture_with: Card | None  # optional: the field card matched by month
    score_delta: int
    note: str

def _matchable(field: List[Card], month: int) -> List[Card]:
    return [c for c in field if c.month==month]

def _score_if_capture(captured_self: List[Card], taken: List[Card]) -> int:
    before = yaku_points(captured_self)
    after = yaku_points(captured_self + taken)
    return after - before

def suggest_best_moves(hand: List[Card], field: List[Card], captured_self: List[Card], captured_opp: List[Card]) -> List[Move]:
    """Greedy one-ply heuristic: prioritize immediate yaku increase, then progress hints, then denial (if two same-month on field)."""
    moves: List[Move] = []
    # For each card, consider capture options
    for h in hand:
        targets = _matchable(field, h.month)
        if not targets:
            # no capture, just place
            moves.append(Move(play=h, capture_with=None, score_delta=0, note="場に出す（取りなし）"))
        else:
            # if there are two or more same-month on field, capturing denies opponent's sweep
            denial_bonus = 1 if len(targets)>=2 else 0
            for t in targets:
                gain = _score_if_capture(captured_self, [h,t])
                note = "役が伸びる" if gain>0 else ("相手の取りを防ぐ" if denial_bonus else "標準取り")
                moves.append(Move(play=h, capture_with=t, score_delta=gain + denial_bonus, note=note))
    # sort by score_delta then tie-break by simple heuristics (prefer bright/animal/ribbon over kasu when equal)
    prio = {"bright":3,"animal":2,"ribbon":1,"kasu":0}
    moves.sort(key=lambda m: (m.score_delta, prio.get(m.play.kind,0)), reverse=True)
    return moves[:5]

def suggest_highest_yaku_line(hand: List[Card], field: List[Card], captured_self: List[Card]) -> List[str]:
    """Return hints focusing on the highest potential yaku (very rough)."""
    hints = list_yaku_progress(captured_self)
    # If we have 2 brights in hand+captured and matching on field, advise
    brights_hand = [c for c in hand if c.kind=="bright"]
    if brights_hand:
        for b in brights_hand:
            if any(f.month==b.month for f in field):
                hints.insert(0, f"光（{b.month}月）を優先して三光/四光/五光を狙う")
                break
    return hints[:5]
