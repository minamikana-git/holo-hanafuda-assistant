from typing import List

# Very small Oicho-Kabu evaluator: value = sum(mod 10), highest closer to 9
# Hanafuda ranks mapping per common rule: months used as ranks (1..12) -> 1..9,10=0,11=0,12=0 (variants exist).
def _rank(month: int) -> int:
    if month<=9: return month % 10
    return 0

def kabu_value(months: List[int]) -> int:
    s = sum(_rank(m) for m in months)
    return s % 10
