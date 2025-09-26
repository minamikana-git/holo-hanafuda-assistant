from dataclasses import dataclass, field
from typing import List, Dict
from .cards import Card, parse_card

@dataclass
class GameState:
    hand: List[Card]
    field: List[Card]
    captured_self: List[Card] = field(default_factory=list)
    captured_opp: List[Card] = field(default_factory=list)
    config: Dict = field(default_factory=dict)

    @staticmethod
    def from_json(data: dict) -> "GameState":
        def conv(lst): return [parse_card(x) if not isinstance(x, Card) else x for x in lst]
        return GameState(
            hand=conv(data.get("hand",[])),
            field=conv(data.get("field",[])),
            captured_self=conv(data.get("captured_self",[])),
            captured_opp=conv(data.get("captured_opp",[])),
            config=data.get("config",{})
        )
