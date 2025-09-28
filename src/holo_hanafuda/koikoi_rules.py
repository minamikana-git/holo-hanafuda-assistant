from collections import Counter, defaultdict
from typing import Dict, List
from .cards import Card

"""
Hololive 版こいこい 役ロジック（添付画像準拠）

- 光
  * 五光: 10
  * 四光: 8（柳以外）
  * 雨入り四光: 7（柳を含む）
  * 三光: 5（柳抜き）
- 花見で一杯（桜の光 + 盃）: 5
- 月見で一杯（月の光 + 盃）: 5
- 猪鹿蝶（イノシカチョウ）: 5
- 赤短（1,2,3 の赤短冊）: 5
- 青短（6,9,10 の青短冊）: 5
- 赤短と青短の重複: 10（※単独の赤短/青短と重複して加点しない実装）
- タネ（動物）: 5枚で1点、以後1枚ごと +1
- タン（短冊）: 5枚で1点、以後1枚ごと +1
- カス: 10枚で1点、以後1枚ごと +1
  ※ホロ特例: 9月のタネ札（盃）をカスとしても数える（タネとカスの両取り）
- 初期手役
  * 手四: 同月4枚が手札にある → 6
  * くっつき: 同月ペア（2枚）が4組以上 → 6
"""

YAKU_POINTS = {
    "gokou": 10,
    "shiko": 8,
    "ame-shiko": 7,
    "sanko": 5,
    "hanami-zake": 5,
    "tsukimi-zake": 5,
    "inoshikacho": 5,
    "akatan": 5,
    "aotan": 5,
    "akatan-aotan": 10,
    "tane": None,
    "tan": None,
    "kasu": None,
    "te-yon": 6,      # 手四
    "kuttsuki": 6,    # くっつき
}

RED_RIBBON_MONTHS = {1, 2, 3}
BLUE_RIBBON_MONTHS = {6, 9, 10}


def _counts(cards: List[Card]) -> Counter:
    """役判定に必要な集計"""
    c: Counter = Counter()
    by_month = defaultdict(int)

    for x in cards:
        by_month[x.month] += 1

        if x.kind == "ribbon":
            if x.tag == "poetry-red":
                c["ribbon-red"] += 1
            elif x.tag == "blue":
                c["ribbon-blue"] += 1
            else:
                c["ribbon"] += 1
        elif x.kind == "animal":
            c["animal"] += 1
            # ホロ特例: 9月の動物（盃）はカスとしても数える
            if x.month == 9 and x.tag == "sake":
                c["kasu-extra"] += 1
        elif x.kind == "kasu":
            c["kasu"] += 1
        elif x.kind == "bright":
            c["bright"] += 1

        if x.tag:
            c[f"tag:{x.tag}"] += 1
        c[f"month:{x.month}"] += 1

    c["total-ribbon"] = c.get("ribbon-red", 0) + c.get("ribbon-blue", 0) + c.get("ribbon", 0)
    c["by_month_pairs"] = sum(by_month[m] // 2 for m in by_month)
    c["any_four_of_month"] = 1 if any(by_month[m] == 4 for m in by_month) else 0
    return c


def _kasu_count_with_holo_rule(captured_counts: Counter) -> int:
    """ホロ特例込みのカス枚数"""
    return captured_counts.get("kasu", 0) + captured_counts.get("kasu-extra", 0)


def evaluate_initial_hand_yaku(hand: List[Card]) -> Dict[str, int]:
    """配られた手札だけで成立する役"""
    if not hand:
        return {}
    c = _counts(hand)
    pts: Dict[str, int] = {}
    if c["any_four_of_month"]:
        pts["te-yon"] = YAKU_POINTS["te-yon"]
    if c["by_month_pairs"] >= 4:
        pts["kuttsuki"] = YAKU_POINTS["kuttsuki"]
    return pts


def evaluate_yaku(
    captured: List[Card],
    *,
    variant: str = "holo",
    initial_hand: List[Card] | None = None
) -> Dict[str, int]:
    """
    取り札からの役判定（＋必要なら初期手役も合算）
    """
    c = _counts(captured)
    pts: Dict[str, int] = {}

    # --- 光 ---
    bright = c.get("bright", 0)
    has_rain = c.get("tag:rain", 0) > 0  # 柳の光
    if bright >= 5:
        pts["gokou"] = YAKU_POINTS["gokou"]
    elif bright == 4:
        pts["ame-shiko" if has_rain else "shiko"] = YAKU_POINTS["ame-shiko" if has_rain else "shiko"]
    elif bright == 3 and not has_rain:
        pts["sanko"] = YAKU_POINTS["sanko"]

    # --- 猪鹿蝶 ---
    if c.get("tag:boar", 0) and c.get("tag:deer", 0) and c.get("tag:butterfly", 0):
        pts["inoshikacho"] = YAKU_POINTS["inoshikacho"]

    # --- 花見・月見 ---
    if c.get("tag:cherry", 0) and c.get("tag:sake", 0):
        pts["hanami-zake"] = YAKU_POINTS["hanami-zake"]
    if c.get("tag:moon", 0) and c.get("tag:sake", 0):
        pts["tsukimi-zake"] = YAKU_POINTS["tsukimi-zake"]

    # --- 赤短・青短・重複 ---
    def _has_ribbon(month: int, tag: str) -> bool:
        return any(
            (x.month == month and x.kind == "ribbon" and x.tag == tag)
            for x in captured
        )

    red_ok = all(_has_ribbon(m, "poetry-red") for m in RED_RIBBON_MONTHS)
    blue_ok = all(_has_ribbon(m, "blue") for m in BLUE_RIBBON_MONTHS)

    if red_ok and blue_ok:
        pts["akatan-aotan"] = YAKU_POINTS["akatan-aotan"]
    else:
        if red_ok:
            pts["akatan"] = YAKU_POINTS["akatan"]
        if blue_ok:
            pts["aotan"] = YAKU_POINTS["aotan"]

    # --- タネ / タン / カス（加点系） ---
    animal_n = c.get("animal", 0)
    if animal_n >= 5:
        pts["tane"] = 1 + (animal_n - 5)

    ribbon_total = c.get("total-ribbon", 0)
    if ribbon_total >= 5:
        pts["tan"] = 1 + (ribbon_total - 5)

    kasu_n = _kasu_count_with_holo_rule(c) if variant == "holo" else c.get("kasu", 0)
    if kasu_n >= 10:
        pts["kasu"] = 1 + (kasu_n - 10)

    # --- 初期手役（任意） ---
    if initial_hand:
        pts.update(evaluate_initial_hand_yaku(initial_hand))

    return pts


def yaku_points(
    captured: List[Card],
    *,
    variant: str = "holo",
    initial_hand: List[Card] | None = None
) -> int:
    e = evaluate_yaku(captured, variant=variant, initial_hand=initial_hand)
    return sum(e.values())


def list_yaku_progress(captured: List[Card], *, variant: str = "holo") -> List[str]:
    """次に狙えるしきい値のヒント（簡易）"""
    c = _counts(captured)
    hints: List[str] = []

    # 光
    bright = c.get("bright", 0)
    has_rain = c.get("tag:rain", 0) > 0
    if bright < 3 or (bright == 3 and has_rain):
        hints.append(f"光 {bright}/3（柳なしで三光）")

    # タネ/タン/カス
    animal_n = c.get("animal", 0)
    if animal_n < 5:
        hints.append(f"タネ {animal_n}/5")

    ribbon_total = c.get("total-ribbon", 0)
    if ribbon_total < 5:
        hints.append(f"タン {ribbon_total}/5")

    kasu_n = _kasu_count_with_holo_rule(c) if variant == "holo" else c.get("kasu", 0)
    if kasu_n < 10:
        hints.append(f"カス {kasu_n}/10")

    # 赤短/青短
    def _has_r(month: int) -> bool:
        return any((x.month == month and x.kind == "ribbon" and x.tag == "poetry-red") for x in captured)
    def _has_b(month: int) -> bool:
        return any((x.month == month and x.kind == "ribbon" and x.tag == "blue") for x in captured)

    red_have = sum(1 for m in RED_RIBBON_MONTHS if _has_r(m))
    blue_have = sum(1 for m in BLUE_RIBBON_MONTHS if _has_b(m))
    if red_have < 3:
        hints.append(f"赤短 {red_have}/3")
    if blue_have < 3:
        hints.append(f"青短 {blue_have}/3")

    # 盃系
    if not (c.get("tag:cherry", 0) and c.get("tag:sake", 0)):
        hints.append("花見で一杯（桜の光 + 盃）")
    if not (c.get("tag:moon", 0) and c.get("tag:sake", 0)):
        hints.append("月見で一杯（月の光 + 盃）")

    return hints
