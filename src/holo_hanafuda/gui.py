import sys
import json
import psutil
from typing import List
from .cards import ALL_CARDS
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QTextEdit, QMessageBox, QGroupBox
)
from .state import GameState
from .koikoi_strategy import suggest_best_moves, suggest_highest_yaku_line
from .koikoi_rules import evaluate_yaku, yaku_points


# ------------------------------
# ユーティリティ
# ------------------------------

MONTHS = [str(i) for i in range(1, 13)]
KINDS = ["bright", "animal", "ribbon", "kasu"]

TAG_OPTIONS = {
    "bright": ["", "crane", "cherry", "moon", "rain", "phoenix"],
    "animal": ["", "nightingale", "cuckoo", "bridge", "butterfly", "boar", "geese", "sake", "deer"],
    "ribbon": ["", "poetry-red", "blue", "plain"],
    "kasu": [""],
}

def token_from_selection(month: str, kind: str, tag: str) -> str:
    """<month>:<kind[-tag]> 形式のトークン文字列を作る"""
    return f"{month}:{kind}" + (f"-{tag}" if tag else "")

def ensure_game_running_or_quit(parent: QWidget | None = None):
    for p in psutil.process_iter(attrs=["name"]):
        n = p.info.get("name") or ""
        if n.lower() == "holoshanafuda.exe":
            return
    QMessageBox.critical(parent, "エラー", "HolosHanafuda.exe が起動していません。\nゲームを起動してから再実行してください。")
    sys.exit(1)


# ------------------------------
# メインウィンドウ
# ------------------------------

class HanafudaGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HolosHanafuda アシスタント")

        ensure_game_running_or_quit(self)

        root = QVBoxLayout(self)

        # --- 入力エリア（カード選択） ---
        sel_box = QGroupBox("カード選択")
        sel_layout = QHBoxLayout()
        sel_box.setLayout(sel_layout)

        self.cmb_month = QComboBox()
        self.cmb_month.addItems(MONTHS)

        self.cmb_kind = QComboBox()
        self.cmb_kind.addItems(KINDS)
        self.cmb_kind.currentTextChanged.connect(self._on_kind_change)

        self.cmb_tag = QComboBox()
        self._refresh_tags(self.cmb_kind.currentText())

        sel_layout.addWidget(QLabel("月"))
        sel_layout.addWidget(self.cmb_month)
        sel_layout.addWidget(QLabel("種別"))
        sel_layout.addWidget(self.cmb_kind)
        sel_layout.addWidget(QLabel("タグ"))
        sel_layout.addWidget(self.cmb_tag)

        # 追加ボタン
        btns = QVBoxLayout()
        self.btn_add_hand = QPushButton("手札に追加")
        self.btn_add_field = QPushButton("場札に追加")
        self.btn_add_self = QPushButton("自分の取札に追加")
        self.btn_add_opp = QPushButton("相手の取札に追加")
        for b in (self.btn_add_hand, self.btn_add_field, self.btn_add_self, self.btn_add_opp):
            btns.addWidget(b)
        sel_layout.addLayout(btns)

        root.addWidget(sel_box)

        # --- リスト表示 ---
        lists_box = QHBoxLayout()

        self.lst_hand = self._make_list_group("手札", "hand")
        self.lst_field = self._make_list_group("場札", "field")
        self.lst_self = self._make_list_group("自分の取札", "captured_self")
        self.lst_opp = self._make_list_group("相手の取札", "captured_opp")

        lists_box.addWidget(self.lst_hand["group"])
        lists_box.addWidget(self.lst_field["group"])
        lists_box.addWidget(self.lst_self["group"])
        lists_box.addWidget(self.lst_opp["group"])

        root.addLayout(lists_box)

        # --- 操作ボタン ---
        ops = QHBoxLayout()
        self.btn_analyze = QPushButton("解析する")
        self.btn_clear = QPushButton("全てクリア")
        ops.addWidget(self.btn_analyze)
        ops.addWidget(self.btn_clear)
        ops.addStretch()
        root.addLayout(ops)

        # --- 結果表示 ---
        root.addWidget(QLabel("解析結果"))
        self.result = QTextEdit()
        self.result.setReadOnly(True)
        root.addWidget(self.result, 1)

        # --- シグナル接続 ---
        self.btn_add_hand.clicked.connect(lambda: self._add_to(self.lst_hand["list"]))
        self.btn_add_field.clicked.connect(lambda: self._add_to(self.lst_field["list"]))
        self.btn_add_self.clicked.connect(lambda: self._add_to(self.lst_self["list"]))
        self.btn_add_opp.clicked.connect(lambda: self._add_to(self.lst_opp["list"]))

        self.lst_hand["remove"].clicked.connect(lambda: self._remove_selected(self.lst_hand["list"]))
        self.lst_field["remove"].clicked.connect(lambda: self._remove_selected(self.lst_field["list"]))
        self.lst_self["remove"].clicked.connect(lambda: self._remove_selected(self.lst_self["list"]))
        self.lst_opp["remove"].clicked.connect(lambda: self._remove_selected(self.lst_opp["list"]))

        self.btn_clear.clicked.connect(self._clear_all)
        self.btn_analyze.clicked.connect(self._analyze)

    # --- UI helpers ---

    def _make_list_group(self, title: str, key: str):
        box = QGroupBox(title)
        v = QVBoxLayout()
        box.setLayout(v)
        lst = QListWidget()
        v.addWidget(lst, 1)
        rm = QPushButton("選択を削除")
        v.addWidget(rm)
        return {"group": box, "list": lst, "remove": rm, "key": key}

    def _on_kind_change(self, kind: str):
        self._refresh_tags(kind)

    def _refresh_tags(self, kind: str):
        self.cmb_tag.clear()
        self.cmb_tag.addItems(TAG_OPTIONS.get(kind, [""]))

    def _add_to(self, lst: QListWidget):
        month = self.cmb_month.currentText()
        kind = self.cmb_kind.currentText()
        tag = self.cmb_tag.currentText()
        token = token_from_selection(month, kind, tag)
        lst.addItem(QListWidgetItem(token))

    def _remove_selected(self, lst: QListWidget):
        for item in lst.selectedItems():
            lst.takeItem(lst.row(item))

    def _clear_all(self):
        for w in (self.lst_hand["list"], self.lst_field["list"], self.lst_self["list"], self.lst_opp["list"]):
            w.clear()
        self.result.clear()

    # --- 解析 ---

    def _collect_state(self) -> dict:
        def items(lst: QListWidget) -> List[str]:
            return [lst.item(i).text() for i in range(lst.count())]
        return {
            "hand": items(self.lst_hand["list"]),
            "field": items(self.lst_field["list"]),
            "captured_self": items(self.lst_self["list"]),
            "captured_opp": items(self.lst_opp["list"]),
            "config": {"variant": "holo"}
        }

    def _analyze(self):
        try:
            data = self._collect_state()
            gs = GameState.from_json(data)

            moves = suggest_best_moves(gs.hand, gs.field, gs.captured_self, gs.captured_opp)
            hints = suggest_highest_yaku_line(gs.hand, gs.field, gs.captured_self)
            
            # 役判定（CLIと同じロジック）
            from .koikoi_rules import evaluate_yaku, yaku_points
            yaku = evaluate_yaku(gs.captured_self, variant="holo", initial_hand=gs.hand)
            total = yaku_points(gs.captured_self, variant="holo", initial_hand=gs.hand)

            lines: List[str] = []
            lines.append("=== 最善手候補 ===")
            if not moves:
                lines.append("(候補なし)")
            else:
                for i, m in enumerate(moves, 1):
                    cap = f" +{m.capture_with.key()}" if m.capture_with else ""
                    lines.append(f"[{i}] {m.play.key()}{cap}  Δscore={m.score_delta}  {m.note}")

            lines.append("\n=== 最高役を狙うヒント ===")
            if not hints:
                lines.append("(なし)")
            else:
                for h in hints:
                    lines.append(f"- {h}")

            lines.append("\n=== 現在の成立役 ===")
            if not yaku:
                lines.append("役は未成立")
            else:
                for k, v in yaku.items():
                    lines.append(f"{k}: {v}")
                lines.append(f"合計: {total} 点")

            # JSON も添付（デバッグ用）
            lines.append("\n=== 入力データ(JSON) ===")
            lines.append(json.dumps(data, ensure_ascii=False, indent=2))

            self.result.setPlainText("\n".join(lines))

        except Exception as e:
            QMessageBox.critical(self, "エラー", f"解析中にエラーが発生しました:\n{e}")
            raise

        def build_tag_options():
            from collections import defaultdict
            tags = defaultdict(set)
            for c in ALL_CARDS:
                if c.kind =="kasu":
                    continue

                if c.tag:
                    tags[c.kind].add(c.tag)

                opts = {
                    "bright": [""] + sorted(tags.get("bright", [])),
                    "animal": [""] + sorted(tags.get("animal", [])),
                    "ribbon": [""] + sorted(tags.get("ribbon", [])),
                    "kasu": [""],
                }
            return opts
        TAG_OPTIONS = build_tag_options()


def main():
    app = QApplication(sys.argv)
    w = HanafudaGUI()
    w.resize(980, 600)
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
# ------------------------------