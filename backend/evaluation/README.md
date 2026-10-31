# Replay boundary evaluation

Stage 2 evaluates gameplay-boundary refinement against permitted local GGST
clips. Keep replay media under the ignored `dev-fixtures/ggst-boundaries/`
directory; do not commit private or unlicensed gameplay.

The committed manifest records labels and reproducibility metadata without
containing local absolute paths. Each case requires:

- a unique `case_id` and relative `clip_filename`;
- `direction` (`start` or `end`);
- validated `coarse_boundary` and manually reviewed `expected_boundary` ranges;
- an `expected_status` of `ok`, `unknown`, or `failed`;
- resolution, frame rate, game patch when known, reviewer role, review date,
  and optional notes.

The manifest configuration records the target tolerance in seconds, the hard
sample limit, and the minimum consecutive likely-HUD samples required before a
transition can tighten. Ambiguous neighboring evidence keeps the result status
`unknown` even when the returned range reaches the target width.

Run the evaluator from `backend/`:

```text
python scripts/evaluate_replay_boundaries.py evaluation/boundary_dataset.v1.json ../dev-fixtures/ggst-boundaries
```

The JSON report includes the dataset, analyzer, configuration, and FFmpeg
versions; coarse and refined boundary error and width; visual-unknown and
technical-failure rates; sample cost; and elapsed processing time.

The manifest is intentionally added only after its clips and labels have been
reviewed. An empty or placeholder dataset is rejected because it cannot support
an accuracy claim.
