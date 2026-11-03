"""Export genuine numerical replay outputs for the static project page."""

import json
from pathlib import Path

from fastrovervla.evaluation import load_config, load_rows, replay

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/site/data"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for dataset in ("orad", "rellis"):
        rows = load_rows(ROOT / f"data/benchmark/{dataset}.jsonl")
        cfg, rule = load_config(ROOT / f"configs/{dataset}_qwen3.json")
        _, full = replay(rows, cfg, rule)
        _, control = replay(rows, cfg, rule, mode="reference", control="no_reuse_correction")
        exported, age = [], 0
        for row, a, b in zip(rows, full, control):
            age = 0 if a["refreshed"] else age + 1
            exported.append({"sequence": row["sequence_id"], "frame_index": row["frame_index"],
                             "refresh": a["refreshed"], "age": age,
                             "budget": row["reference_reuse_budget"], "speed": row["observed_action"][0],
                             "gt": row["ground_truth"], "full": a["waypoints"], "control": b["waypoints"],
                             "fde": a["fde"], "control_fde": b["fde"]})
        (OUT / f"{dataset}.json").write_text(json.dumps(exported, separators=(",", ":")) + "\n", encoding="utf-8", newline="\n")
        print(f"Exported {len(exported)} {dataset} windows")


if __name__ == "__main__":
    main()
