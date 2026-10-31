"""Run the Stage 2 boundary evaluator against permitted local GGST clips."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.services.replay_boundary_evaluation import (
    evaluate_boundary_dataset,
    evaluation_report_as_dict,
    load_boundary_evaluation_dataset,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to the versioned boundary-evaluation manifest.")
    parser.add_argument("media_root", type=Path, help="Directory containing the permitted local clips.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    dataset = load_boundary_evaluation_dataset(args.manifest)
    report = evaluate_boundary_dataset(dataset, args.media_root)
    print(json.dumps(evaluation_report_as_dict(report), indent=2))


if __name__ == "__main__":
    main()
