"""Small portable entry points for the release package."""

import argparse
import csv
import json
from dataclasses import asdict
from pathlib import Path

from .evaluation import load_config, load_rows, replay
from .execution import FastRoverPolicy, FrameContext


def main() -> None:
    parser = argparse.ArgumentParser(description="FastRoverVLA recurrent execution")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Run a synthetic callback example (no model weights)")
    demo.add_argument("--steps", type=int, default=24)
    evaluate = sub.add_parser("replay", help="Evaluate frozen predictions; makes no model requests")
    evaluate.add_argument("--input", type=Path, required=True)
    evaluate.add_argument("--config", type=Path, required=True)
    evaluate.add_argument("--mode", choices=["every", "fixed", "adaptive", "reference"], default="adaptive")
    evaluate.add_argument("--control", default="full")
    evaluate.add_argument("--target", choices=["ground_truth", "past_heading_ground_truth"], default="ground_truth")
    evaluate.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "demo":
        if args.steps <= 0:
            parser.error("--steps must be positive")
        policy = FastRoverPolicy()
        for i in range(args.steps):
            result = policy.step(FrameContext("synthetic", 1.0 + i * 0.01, 0.02),
                                 lambda _: [(1.2, 0.025)] * 6)
            print(json.dumps({"step": i, **asdict(result)}))
        return
    cfg, refresh = load_config(args.config)
    rows = load_rows(args.input)
    if args.output.resolve() in {args.input.resolve(), args.config.resolve()}:
        parser.error("--output must not overwrite an input file")
    summary, predictions = replay(rows, cfg, refresh, mode=args.mode, target=args.target, control=args.control)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (args.output / "predictions.jsonl").write_text(
        "".join(json.dumps(row) + "\n" for row in predictions), encoding="utf-8")
    with (args.output / "per_window.csv").open("w", encoding="utf-8", newline="") as stream:
        columns = ["id", "sequence_id", "frame_index", "refreshed", "ade", "fde", "rmse", "l2"]
        writer = csv.DictWriter(stream, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(predictions)
    print(json.dumps(summary, indent=2))
