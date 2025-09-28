from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Tuple

from .cards import Card, parse_card

# ───────────────────────────────────────────────────────────
# 役仕様
# ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HoloRole:
    id: str                 # 内部ID
    title: str              # 表示名（日本語）
    requires: Tuple[str,...]# 必要な札（トークン文字列）※AND条件
    description: str        # 効果の説明（人間向け）
    hint: str               # GUI に出す簡単な指示

# ここでは「検出ロジック」と「説明文」を実装。
# 実際のカード操作（どの札を選ぶ/捨てる等）は、GUI側で選択UIを用意してから適用する想定。
# ※トークン表記は '<month>:<kind[-tag]>'。cards.py に合わせて記述します。

HOLO_ROLES: List[HoloRole] = [
    # 0 期生（例：1月セット想定）※必要札は適宜更新してください
    HoloRole(
        id="gen0",
        title="0期生",
        requires=("1:bright-crane", "1:ribbon-poetry-red", "1:kasu"),
        description="場札から1枚を選び、手札に加える。",
        hint="場から任意の1枚を選んで手札へ移動",
    ),
    # 1 期生
    HoloRole(
        id="gen1",
        title="1期生",
        requires=("2:animal-nightingale", "2:ribbon-poetry-red", "2:kasu"),
        description="相手の手札を公開（2ターン）。",
        hint="2ターンの間、相手手札を公開扱い",
    ),
    # 2 期生
    HoloRole(
        id="gen2",
        title="2期生",
        requires=("3:bright-cherry", "3:ribbon-poetry-red", "3:kasu"),
        description="場札1枚をロック（2ターン後に解除）。",
        hint="場から1枚を指定してロック",
    ),
    # 3 期生
    HoloRole(
        id="gen3",
        title="3期生",
        requires=("4:animal-cuckoo", "4:ribbon-plain", "4:kasu"),
        description="次のターンを自分のターンにする（手番スキップ）。",
        hint="相手の手番を飛ばして自分の手番",
    ),
    # 4 期生
    HoloRole(
        id="gen4",
        title="4期生",
        requires=("5:animal-bridge", "5:ribbon-plain", "5:kasu"),
        description="山札から1枚引き、手札に加える。",
        hint="山から1枚ドローして手札へ",
    ),
    # 5 期生
    HoloRole(
        id="gen5",
        title="5期生",
        requires=("6:animal-butterfly", "6:ribbon-blue", "6:kasu"),
        description="相手の手札から1枚選んで場に捨てさせる。",
        hint="相手手札から1枚を指定し場へ",
    ),
    # 秘密結社 holoX
    HoloRole(
        id="holoX",
        title="秘密結社holoX",
        requires=("7:animal-boar", "8:animal-geese", "9:animal-sake", "10:animal-deer"),
        description="すべての場札を山に戻し、シャッフルして並べなおす。",
        hint="場を全戻し→山をシャッフル→再配置",
    ),
    # ホロライブゲーマーズ
    HoloRole(
        id="gamers",
        title="ゲーマーズ",
        requires=("8:bright-moon", "9:ribbon-blue", "12:ribbon-plain"),  # ←仮。必要に応じて更新
        description="自分と相手の手札を入れ替える。",
        hint="手札をまるごと交換",
    ),
    # ReGLOSS
    HoloRole(
        id="regloss",
        title="ReGLOSS",
        requires=("11:bright-rain", "11:animal-swallow", "11:ribbon-plain"),
        description="相手の手札1枚を、役が成立しない札にする（捨て札になると解除）。",
        hint="相手手札の1枚を“無効札”指定",
    ),
]

# ───────────────────────────────────────────────────────────
# 検出
# ───────────────────────────────────────────────────────────

def _have_tokens(captured: List[Card], required: Tuple[str,...]) -> bool:
    """required の全トークンを captured が満たすか（AND）"""
    captured_keys = {f"{c.month}:{c.kind}{('-'+c.tag) if c.tag else ''}" for c in captured}
    # カスが複数必要など、将来の拡張のために回数も見たい場合はカウント方式に変更する
    return all(r in captured_keys for r in required)

def detect_holo_roles(captured: List[Card]) -> List[HoloRole]:
    """取り札から成立しているホロ役を列挙"""
    res: List[HoloRole] = []
    for role in HOLO_ROLES:
        if _have_tokens(captured, role.requires):
            res.append(role)
    return res
# ───────────────────────────────────────────────────────────