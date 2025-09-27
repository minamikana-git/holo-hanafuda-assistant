from collections import Counter, defaultdict
from typing import Dict, List, Tuple
from .cards import Card

"""
Hololive版こいこい 役ロジック（画像資料準拠）
- 三光は「柳(11月の光)を除く3枚」
- 四光は「柳以外の光4枚」
- 雨入り四光は「柳を含む光4枚」
- 花見で一杯(桜の光 + 盃) 5点
- 月見で一杯(月の光 + 盃) 5点
- 赤短: 1,2,3 月の短冊 3枚で 5点（以降の短冊はタンの加点へ）
- 青短: 6,9,10 月の短冊 3枚で 5点
- 赤短と青短の重複: 10点（※赤短・青短の単独は同時に数えない想定）
- タネ(動物) 5枚で 1点、以降1枚ごとに +1
- タン(短冊) 5枚で 1点、以降1枚ごとに +1
- カス 10枚で 1点、以降1枚ごとに +1
  ※「9月のタネ札（盃）」もカス札として数える（動物カウントは減らさない）
- 初期手役:
  - 手四: 配られた手札に同じ月が4枚 → 6点
  - くっつき: 手札の同月ペア(2枚)の組が4組以上 → 6点
"""

# 画像の点数に合わせた定義
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
    # 加点系は下で計算
    "tane": None,
    "tan": None,
    "kasu": None,
    # 初期手役
    "te-shi": 6,
    "kuttsuki": 6,
}

RED_RIBBON_MONTHS = {1, 2, 3}       # 赤短
BLUE_RIBBON_MONTHS = {6, 9, 10}     # 青短


def _counts(cards: List[Card]) -> Dict[str, int]:
    """役判定に使う集計（種別・タグ・月ごとなど）"""
    c = Counter()
    by_month = defaultdict(int)
    for x in cards:
        by_month[x.month] += 1
        if x.kind == "ribbon":
            # 短冊の色別
            if x.tag == "poetry-red":
                c["ribbon-red"] += 1
            elif x.tag == "blue":
                c["ribbon-blue"] += 1
            else:
                c["ribbon"] += 1
        else:
            c[x.kind] += 1
        if x.tag:
            c[f"tag:{x.tag}"] += 1
        c[f"month:{x.month}"] += 1

    # 便利カウント
    c["total-ribbon"] = c.get("ribbon-red", 0) + c.get("ribbon-blue", 0) + c.get("ribbon", 0)
    c["by_month_pairs"] = sum(by_month[m] // 2 for m in by_month)  # くっつき用
    c["any_four_of_month"] = 1 if any(by_month[m] == 4 for m in by_month) else 0  # 手四用
    return c


def _kasu_count_with_holo_rule(captured: List[Card]) -> int:
    """カス枚数（ホロ変種：9月のタネ札もカスとして数える）"""
    base = sum(1 for x in captured if x.kind == "kasu")
    # 9月のタネ札（盃）をカスとしてもカウント
    extra = sum(1 for x in captured if (x.month == 9 and x.kind == "animal"))
    return base + extra


def evaluate_initial_hand_yaku(hand: List[Card]) -> Dict[str, int]:
    """配られた手札だけで成立する役（手四・くっつき）"""
    if not hand:
        return {}
    h = _counts(hand)
    pts = {}
    if h["any_four_of_month"]:
        pts["te-shi"] = YAKU_POINTS["te-shi"]
    if h["by_month_pairs"] >= 4:
        pts["kuttsuki"] = YAKU_POINTS["kuttsuki"]
    return pts


def evaluate_yaku(
    captured: List[Card],
    *,
    variant: str = "holo",
    initial_hand: List[Card] | None = None
) -> Dict[str, int]:
    """
    取り札からの役判定（＋必要なら初期手役も合算）。
    variant は将来拡張用（現状 "holo" 固定）。
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

    # --- 花見・月見（盃との組み合わせ） ---
    if c.get("tag:cherry", 0) and c.get("tag:sake", 0):
        pts["hanami-zake"] = YAKU_POINTS["hanami-zake"]
    if c.get("tag:moon", 0) and c.get("tag:sake", 0):
        pts["tsukimi-zake"] = YAKU_POINTS["tsukimi-zake"]

    # --- 短冊（赤短・青短・重複）---
    # 画像準拠：赤短(1,2,3) 3枚で5点 / 青短(6,9,10) 3枚で5点 / 重複10点
    # より堅牢に：月×色で直接検索
        # --- 短冊（赤短・青短・重複）---
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

    # --- 加点系（タネ/タン/カス） ---
    animal_n = c.get("animal", 0)
    if animal_n >= 5:
        pts["tane"] = 1 + (animal_n - 5)

    ribbon_total = c.get("total-ribbon", 0)
    if ribbon_total >= 5:
        pts["tan"] = 1 + (ribbon_total - 5)

    kasu_n = _kasu_count_with_holo_rule(captured) if variant == "holo" else c.get("kasu", 0)
    if kasu_n >= 10:
        pts["kasu"] = 1 + (kasu_n - 10)

    # --- 初期手役（任意） ---
    if initial_hand:
        init_pts = evaluate_initial_hand_yaku(initial_hand)
        pts.update(init_pts)

    return pts


def yaku_points(captured: List[Card], *, variant: str = "holo", initial_hand: List[Card] | None = None) -> int:
    e = evaluate_yaku(captured, variant=variant, initial_hand=initial_hand)
    return sum(e.values())


def list_yaku_progress(captured: List[Card], *, variant: str = "holo") -> List[str]:
    """次に狙えるしきい値のヒント（簡易）"""
    c = _counts(captured)
    hints = []

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

    kasu_n = _kasu_count_with_holo_rule(captured) if variant == "holo" else c.get("kasu", 0)
    if kasu_n < 10:
        hints.append(f"カス {kasu_n}/10")

    # 赤短/青短
    red_have = sum(1 for m in RED_RIBBON_MONTHS if any((x.month == m and x.kind == "ribbon" and x.tag == "poetry-red") for x in captured))
    blue_have = sum(1 for m in BLUE_RIBBON_MONTHS if any((x.month == m and x.kind == "ribbon" and x.tag == "blue") for x in captured))
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
