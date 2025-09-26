import json, argparse, sys
from .state import GameState
from .koikoi_rules import evaluate_yaku, yaku_points
from .koikoi_strategy import suggest_best_moves, suggest_highest_yaku_line
from .oicho_kabu import kabu_value

def cmd_suggest(path: str):
    data = json.load(open(path, "r", encoding="utf-8"))
    gs = GameState.from_json(data)
    moves = suggest_best_moves(gs.hand, gs.field, gs.captured_self, gs.captured_opp)
    for i,m in enumerate(moves,1):
        cap = f" +{m.capture_with.key()}" if m.capture_with else ""
        print(f"[{i}] {m.play.key()}{cap}  Δscore={m.score_delta}  {m.note}")
    print("\n最高役ライン:", *suggest_highest_yaku_line(gs.hand, gs.field, gs.captured_self), sep="\n - ")

def cmd_eval_yaku(path: str):
    data = json.load(open(path, "r", encoding="utf-8"))
    gs = GameState.from_json(data)
    y = evaluate_yaku(gs.captured_self)
    total = yaku_points(gs.captured_self)
    if not y:
        print("役は未成立")
    else:
        for k,v in y.items():
            print(f"{k}: {v}")
        print(f"合計: {total} 点")

def cmd_kabu(nums):
    months = [int(x) for x in nums]
    print(f"おいちょかぶ値: {kabu_value(months)}")

def main(argv=None):
    p = argparse.ArgumentParser(prog="hanafuda", description="Holo Hanafuda Assistant CLI")
    sub = p.add_subparsers(dest="cmd", required=True)
    s1 = sub.add_parser("suggest", help="最善手候補の表示")
    s1.add_argument("state_json")
    s2 = sub.add_parser("eval-yaku", help="現在の役の判定")
    s2.add_argument("state_json")
    s3 = sub.add_parser("kabu", help="おいちょかぶの値（例: kabu 12 8 3）")
    s3.add_argument("months", nargs="+")
    args = p.parse_args(argv)
    if args.cmd=="suggest": cmd_suggest(args.state_json)
    elif args.cmd=="eval-yaku": cmd_eval_yaku(args.state_json)
    elif args.cmd=="kabu": cmd_kabu(args.months)

if __name__ == "__main__":
    main()
