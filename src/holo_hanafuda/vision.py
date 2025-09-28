# src/holo_hanafuda/vision.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple, Iterable
import numpy as np
import cv2
import mss

TEMPLATE_DIR = Path(__file__).resolve().parents[2] / "assets" / "templates"

@dataclass
class Detection:
    token: str
    score: float
    bbox: Tuple[int, int, int, int]  # x,y,w,h（scene内座標）

def _filename_to_token(p: Path) -> str:
    stem = p.stem  # e.g., "11_animal_swallow"
    parts = stem.split("_")
    if len(parts) == 3:
        month, kind, tag = parts
        return f"{int(month)}:{kind}-{tag}"
    elif len(parts) == 2:
        month, kind = parts
        return f"{int(month)}:{kind}"
    raise ValueError(f"Invalid template filename: {p.name}")

def load_templates(dirpath: Path | str = TEMPLATE_DIR) -> Dict[str, np.ndarray]:
    dirpath = Path(dirpath)
    tmps: Dict[str, np.ndarray] = {}
    if not dirpath.exists():
        return tmps
    for p in sorted(dirpath.glob("*.png")):
        img = cv2.imread(str(p), cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        tmps[_filename_to_token(p)] = img
    return tmps

def grab_screen(region: Tuple[int,int,int,int] | None = None) -> np.ndarray:
    """region=(left, top, width, height) / None=プライマリ全体。返り値はBGR"""
    with mss.mss() as sct:
        mon = region if region else sct.monitors[1]
        raw = sct.grab(mon)
        img = np.array(raw)  # BGRA
        return img[..., :3]  # BGR

def match_templates(
    scene_bgr: np.ndarray,
    templates: Dict[str, np.ndarray],
    threshold: float = 0.88,
    scales: Iterable[float] = (1.0, 0.9, 1.1)
) -> List[Detection]:
    scene_gray = cv2.cvtColor(scene_bgr, cv2.COLOR_BGR2GRAY)
    dets: List[Detection] = []
    for token, tpl0 in templates.items():
        for s in scales:
            tpl = cv2.resize(tpl0, None, fx=s, fy=s, interpolation=cv2.INTER_AREA if s < 1.0 else cv2.INTER_CUBIC)
            h, w = tpl.shape[:2]
            if h >= scene_gray.shape[0] or w >= scene_gray.shape[1]:
                continue
            res = cv2.matchTemplate(scene_gray, tpl, cv2.TM_CCOEFF_NORMED)
            ys, xs = np.where(res >= threshold)
            for (x, y) in zip(xs, ys):
                dets.append(Detection(token=token, score=float(res[y, x]), bbox=(int(x), int(y), int(w), int(h))))
    # 簡易NMSで重複除去
    dets.sort(key=lambda d: d.score, reverse=True)
    kept: List[Detection] = []
    def iou(a: Detection, b: Detection) -> float:
        ax, ay, aw, ah = a.bbox
        bx, by, bw, bh = b.bbox
        x1, y1 = max(ax, bx), max(ay, by)
        x2, y2 = min(ax+aw, bx+bw), min(ay+ah, by+bh)
        inter = max(0, x2-x1) * max(0, y2-y1)
        union = aw*ah + bw*bh - inter + 1e-6
        return inter / union
    for d in dets:
        if all(iou(d, k) < 0.3 for k in kept):
            kept.append(d)
    return kept
