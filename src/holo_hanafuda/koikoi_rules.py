from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from .cards import Card

# Basic Koi-Koi yaku thresholds (simplified, points without multiplier/koikoi chaining)
YAKU_DEF = {
    "gokou": {"bright":5, "points":10},
    "shiko": {"bright":4, "points":8},  # no rain
    "ame-shiko": {"bright":4, "points":7},  # including rain
    "sanko": {"bright":3, "points":5},
    "inoshikacho": {"tags":{"boar","deer","butterfly"}, "points":5},
    "akatan": {"ribbon-red":3, "points":3},
    "aotan": {"ribbon-blue":3, "points":3},
    "akatan-aotan": {"ribbon-red":3, "ribbon-blue":3, "points":6},
    "tane": {"animal":5, "points":1, "extra":1},   # 1 + (n-5)
    "tan": {"ribbon":5, "points":1, "extra":1},
    "kasu": {"kasu":10, "points":1, "extra":1},
    "hanami-zake": {"tags":{"cherry","sake"}, "points":3},
    "tsukimi-zake": {"tags":{"moon","sake"}, "points":3}
}

def _counts(cards: List[Card]) -> Dict[str, int]:
    c = Counter()
    for x in cards:
        k = x.kind
        if k=="ribbon":
            if x.tag=="poetry-red": c["ribbon-red"] += 1
            elif x.tag=="blue": c["ribbon-blue"] += 1
            else: c["ribbon"] += 1
        else:
            c[k] += 1
        if x.tag:
            c[f"tag:{x.tag}"] += 1
    return c

def evaluate_yaku(captured: List[Card]) -> Dict[str, int]:
    """Return dict of yaku -> points (sum extra where applicable)."""
    c = _counts(captured)
    pts: Dict[str,int] = {}
    bright = c.get("bright",0)
    has_rain = c.get("tag:rain",0) > 0
    if bright>=5:
        pts["gokou"]=YAKU_DEF["gokou"]["points"]
    elif bright==4:
        pts["shiko" if not has_rain else "ame-shiko"] = YAKU_DEF["shiko"]["points" if not has_rain else "points"] if not has_rain else YAKU_DEF["ame-shiko"]["points"]
    elif bright==3:
        pts["sanko"]=YAKU_DEF["sanko"]["points"]
    # Inoshikacho
    if c.get("tag:boar",0) and c.get("tag:deer",0) and c.get("tag:butterfly",0):
        pts["inoshikacho"] = YAKU_DEF["inoshikacho"]["points"]
    # ribbons
    if c.get("ribbon-red",0)>=3 and c.get("ribbon-blue",0)>=3:
        pts["akatan-aotan"]=YAKU_DEF["akatan-aotan"]["points"]
    else:
        if c.get("ribbon-red",0)>=3:
            pts["akatan"]=YAKU_DEF["akatan"]["points"]
        if c.get("ribbon-blue",0)>=3:
            pts["aotan"]=YAKU_DEF["aotan"]["points"]
    # animals/tane
    if c.get("animal",0)>=5:
        pts["tane"] = YAKU_DEF["tane"]["points"] + (c.get("animal",0)-5)*YAKU_DEF["tane"]["extra"]
    # ribbons (all)
    total_ribbon = c.get("ribbon-red",0)+c.get("ribbon-blue",0)+c.get("ribbon",0)
    if total_ribbon>=5:
        pts["tan"] = YAKU_DEF["tan"]["points"] + (total_ribbon-5)*YAKU_DEF["tan"]["extra"]
    # kasu
    if c.get("kasu",0)>=10:
        pts["kasu"] = YAKU_DEF["kasu"]["points"] + (c.get("kasu",0)-10)*YAKU_DEF["kasu"]["extra"]
    # sake combos
    if c.get("tag:sake",0):
        if c.get("tag:cherry",0):
            pts["hanami-zake"]=YAKU_DEF["hanami-zake"]["points"]
        if c.get("tag:moon",0):
            pts["tsukimi-zake"]=YAKU_DEF["tsukimi-zake"]["points"]
    return pts

def yaku_points(captured: List[Card]) -> int:
    e = evaluate_yaku(captured)
    return sum(e.values())

def list_yaku_progress(captured: List[Card]) -> List[str]:
    """Return human-readable hints toward next yaku thresholds."""
    c = _counts(captured)
    hints = []
    if c.get("animal",0)<5:
        hints.append(f"動物 {c.get('animal',0)}/5")
    total_ribbon = c.get("ribbon-red",0)+c.get("ribbon-blue",0)+c.get("ribbon",0)
    if total_ribbon<5:
        hints.append(f"短冊 {total_ribbon}/5")
    if c.get("kasu",0)<10:
        hints.append(f"カス {c.get('kasu',0)}/10")
    if c.get("ribbon-red",0)<3:
        hints.append(f"赤短 {c.get('ribbon-red',0)}/3")
    if c.get("ribbon-blue",0)<3:
        hints.append(f"青短 {c.get('ribbon-blue',0)}/3")
    if c.get("bright",0)<3:
        hints.append(f"三光 {c.get('bright',0)}/3（雨含まず）")
    return hints
