import sys
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QHBoxLayout
)

from holo_hanafuda.state import GameState
from holo_hanafuda.koikoi_strategy import suggest_best_moves
from holo_hanafuda.koikoi_rules import evaluate_yaku, yaku_points
from holo_hanafuda.cards import parse_card


class HanafudaGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HolosHanafuda アシスタント")

        layout = QVBoxLayout()

        self.state_input = QTextEdit()
        self.state_input.setPlaceholderText("ここにJSONを入力 (手札・場札・取札など)")
        layout.addWidget(QLabel("局面JSON入力"))
        layout.addWidget(self.state_input)

        btn_layout = QHBoxLayout()
        self.btn_analyze = QPushButton("解析する")
        self.btn_analyze.clicked.connect(self.analyze)
        btn_layout.addWidget(self.btn_analyze)
        layout.addLayout(btn_layout)

        self.result = QTextEdit()
        self.result.setReadOnly(True)
        layout.addWidget(QLabel("解析結果"))
        layout.addWidget(self.result)

        self.setLayout(layout)

    def analyze(self):
        try:
            data = json.loads(self.state_input.toPlainText())
            gs = GameState.from_json(data)
            moves = suggest_best_moves(gs.hand, gs.field, gs.captured_self, gs.captured_opp)
            yaku = evaluate_yaku(gs.captured_self)
            total = yaku_points(gs.captured_self)

            text = []
            text.append("=== 最善手候補 ===")
            for i, m in enumerate(moves, 1):
                cap = f" +{m.capture_with.key()}" if m.capture_with else ""
                text.append(f"[{i}] {m.play.key()}{cap} Δscore={m.score_delta} {m.note}")

            text.append("\n=== 成立役 ===")
            if not yaku:
                text.append("役は未成立")
            else:
                for k, v in yaku.items():
                    text.append(f"{k}: {v}")
                text.append(f"合計: {total} 点")

            self.result.setPlainText("\n".join(text))

        except Exception as e:
            self.result.setPlainText(f"エラー: {e}")


def main():
    app = QApplication(sys.argv)
    win = HanafudaGUI()
    win.resize(600, 400)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
