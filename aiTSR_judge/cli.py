#!/usr/bin/env python3
# aiTSR v3.1 — CLI entrypoint
# Usage: python -m aiTSR_judge input.csv output.csv [options]
from __future__ import annotations
import argparse
import sys
import pandas as pd

from .judge import AiTSRJudge
from .schemas import JudgeInput, JudgeOutput


def main():
    parser = argparse.ArgumentParser(
        prog="python -m aiTSR_judge",
        description="aiTSR v3.1 — LLM-as-a-judge rubric scorer (Claude Opus 4)",
    )
    parser.add_argument("input_csv",  help="Input CSV (must have: utterance, response, ground_truth)")
    parser.add_argument("output_csv", help="Output CSV path (input cols + score cols appended)")
    parser.add_argument("--model",    default="claude-opus-4-5", help="Claude model name")
    parser.add_argument("--no-thinking", action="store_true",
                        help="Disable extended thinking (faster, cheaper)")
    parser.add_argument("--thinking-budget", type=int, default=10_000,
                        help="Extended thinking token budget (default: 10000)")
    parser.add_argument("--api-key",  default=None,
                        help="Anthropic API key (default: ANTHROPIC_API_KEY env var)")
    parser.add_argument("--max-retries", type=int, default=3,
                        help="Max retries per row on parse/API error (default: 3)")
    args = parser.parse_args()

    # ── load input ────────────────────────────────────────────────
    try:
        df = pd.read_csv(args.input_csv)
    except Exception as e:
        print(f"ERROR: Could not read input CSV: {e}", file=sys.stderr)
        sys.exit(1)

    required_cols = {"utterance", "response", "ground_truth"}
    missing = required_cols - set(df.columns)
    if missing:
        print(f"ERROR: Input CSV is missing required columns: {missing}", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {len(df)} rows from {args.input_csv}")
    optional_present = [c for c in ["prior_context", "grounding_context", "request_time"] if c in df.columns]
    if optional_present:
        print(f"Optional columns detected: {optional_present}")

    # ── build judge ───────────────────────────────────────────────
    judge = AiTSRJudge(
        api_key=args.api_key,
        model=args.model,
        extended_thinking=not args.no_thinking,
        thinking_budget=args.thinking_budget,
        max_retries=args.max_retries,
    )

    mode = "extended thinking" if not args.no_thinking else "no thinking"
    print(f"Judge: {args.model} ({mode})\n")

    # ── score rows ────────────────────────────────────────────────
    inputs = []
    for _, row in df.iterrows():
        try:
            inputs.append(JudgeInput.from_csv_row(row.to_dict()))
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            sys.exit(1)

    outputs = judge.score_batch(inputs, progress=True)

    # ── write output ──────────────────────────────────────────────
    out_df = df.copy()
    for col in JudgeOutput.OUTPUT_COLUMNS:
        out_df[col] = [getattr(o, col, None) for o in outputs]

    # Drop error column if no errors occurred
    if all(o.error is None for o in outputs):
        out_df.drop(columns=["error"], inplace=True, errors="ignore")

    out_df.to_csv(args.output_csv, index=False)

    # ── summary ───────────────────────────────────────────────────
    verdicts = [o.verdict for o in outputs]
    n_pass  = verdicts.count("PASS")
    n_fail  = verdicts.count("FAIL")
    n_error = verdicts.count("ERROR")
    total   = len(outputs)

    print(f"\n── Results ──────────────────────")
    print(f"  PASS  : {n_pass:>4} / {total}  ({100*n_pass/total:.1f}%)")
    print(f"  FAIL  : {n_fail:>4} / {total}  ({100*n_fail/total:.1f}%)")
    if n_error:
        print(f"  ERROR : {n_error:>4} / {total}")
    print(f"\nOutput written to: {args.output_csv}")


if __name__ == "__main__":
    main()
