# tools/slice_hanafuda_grid.py
import argparse
from pathlib import Path
import cv2
import numpy as np

"""
12か月×4枚の一覧画像を 48 枚のテンプレートに切り出して保存します。
レイアウト前提：
  行：3行（上 1/4/7/10 月、中央 2/5/8/11 月、下 3/6/9/12 月）
  列：各行 4つの「月ブロック」
  各「月ブロック」の中に 左→右 に 4枚のカード

縦横マージンや隙間は画像解像度に対する比率で指定でき、
ズレがあれば CONST を微調整してください（調整ポイントは下）。
"""

# ======= 調整ポイント（必要に応じて微調整） =======
# 一覧画像の外枠マージン（比率）
TOP_MARGIN   = 0.07
BOTTOM_MARGIN= 0.06
LEFT_MARGIN  = 0.02
RIGHT_MARGIN = 0.02

# 行間（行ブロックの隙間）と列間（列ブロックの隙間）の比率
ROW_GAP_RATIO = 0.06
COL_GAP_RATIO = 0.015

# 月ブロック内で、カード4枚の左右マージン・隙間（比率・相対）
INBLOCK_LEFT_PAD  = 0.02
INBLOCK_RIGHT_PAD = 0.02
INBLOCK_GAP_RATIO = 0.02
# ================================================

# 月→カードの命名（左→右）
# 画像の並び順（左→右）に合わせています。一般的な配列を想定。
MONTH_CARDS = {
    1:  ["bright:crane",         "ribbon:poetry-red", "kasu", "kasu"],
    2:  ["animal:nightingale",   "ribbon:poetry-red", "kasu", "kasu"],
    3:  ["bright:cherry",        "ribbon:poetry-red", "kasu", "kasu"],
    4:  ["animal:cuckoo",        "ribbon:plain",      "kasu", "kasu"],
    5:  ["animal:bridge",        "ribbon:plain",      "kasu", "kasu"],
    6:  ["animal:butterfly",     "ribbon:blue",       "kasu", "kasu"],
    7:  ["animal:boar",          "ribbon:plain",      "kasu", "kasu"],
    8:  ["bright:moon",          "animal:geese",      "kasu", "kasu"],
    9:  ["animal:sake",          "ribbon:blue",       "kasu", "kasu"],
    10: ["animal:deer",          "ribbon:blue",       "kasu", "kasu"],
    11: ["bright:rain",          "animal:swallow",    "ribbon:plain", "kasu"],
    12: ["bright:phoenix",       "kasu",              "kasu",         "kasu"],
}

# 行ごとの月（画像の並びに合わせる）
ROWS_TO_MONTHS = [
    [1, 4, 7, 10],   # 上段
    [2, 5, 8, 11],   # 中段
    [3, 6, 9, 12],   # 下段
]

def slice_grid(src_path: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    img = cv2.imread(str(src_path))
    if img is None:
        raise FileNotFoundError(f"cannot read image: {src_path}")

    H, W = img.shape[:2]

    # 外枠を除いた有効領域
    x0 = int(W * LEFT_MARGIN)
    x1 = W - int(W * RIGHT_MARGIN)
    y0 = int(H * TOP_MARGIN)
    y1 = H - int(H * BOTTOM_MARGIN)

    roi = img[y0:y1, x0:x1].copy()
    RH, RW = roi.shape[:2]

    # 行ブロック・列ブロックのサイズ算出
    row_gap = int(RH * ROW_GAP_RATIO)
    col_gap = int(RW * COL_GAP_RATIO)

    row_block_h = (RH - row_gap * 2) // 3          # 3行
    col_block_w = (RW - col_gap * 3) // 4          # 4列（各行の月ブロック）

    # 月ブロック内でカード4枚の横配置
    padL = int(col_block_w * INBLOCK_LEFT_PAD)
    padR = int(col_block_w * INBLOCK_RIGHT_PAD)
    in_gap = int(col_block_w * INBLOCK_GAP_RATIO)
    usable_w = col_block_w - padL - padR - in_gap * 3
    card_w = usable_w // 4

    # カード高は月ブロックの高さいっぱい（上下少し余裕みるなら係数を掛ける）
    card_h = row_block_h

    # 切り取りと保存
    for r, months in enumerate(ROWS_TO_MONTHS):
        for c, month in enumerate(months):
            # 月ブロックの左上
            bx = c * (col_block_w + col_gap)
            by = r * (row_block_h + row_gap)

            for k in range(4):  # 左→右 4枚
                cx = padL + k * (card_w + in_gap)
                cy = 0
                x = bx + cx
                y = by + cy
                card = roi[y:y+card_h, x:x+card_w]

                # ファイル名
                kind_tag = MONTH_CARDS[month][k]
                if ":" in kind_tag:
                    kind, tag = kind_tag.split(":")
                    fname = f"{month}_{kind}_{tag}.png"
                else:
                    # kasu のとき、同月内の重複を区別（_2, _3 を付ける）
                    existing = list(out_dir.glob(f"{month}_kasu*.png"))
                    if len(existing) == 0:
                        fname = f"{month}_kasu.png"
                    else:
                        fname = f"{month}_kasu_{len(existing)+1}.png"

                cv2.imwrite(str(out_dir / fname), card)

    print(f"[done] saved 48 templates into: {out_dir}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="一覧画像のパス（例: assets/source/holo_cards_grid.png）")
    ap.add_argument("--out", default="assets/templates", help="出力先フォルダ（既定: assets/templates）")
    args = ap.parse_args()

    slice_grid(Path(args.src), Path(args.out))

if __name__ == "__main__":
    main()
