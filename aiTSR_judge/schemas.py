# aiTSR v3.1 — Input / Output schemas
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Optional
import pandas as pd


@dataclass
class JudgeInput:
    """One row of input to the rubric judge."""
    utterance: str                          # user's spoken query (ASR text)
    response: str                           # assistant response being evaluated
    ground_truth: str                       # consensus ground truth reference

    # Optional — auto-detected from CSV if present
    prior_context: Optional[str] = None    # prior conversation turns
    grounding_context: Optional[str] = None  # weather/location/search results
    request_time: Optional[str] = None     # ISO timestamp of original request

    # Carry-through: any extra CSV columns are kept here for output
    _extra: dict = field(default_factory=dict, repr=False)

    @classmethod
    def from_csv_row(cls, row: dict) -> "JudgeInput":
        """Build a JudgeInput from a CSV row dict, auto-detecting optional cols."""
        required = {"utterance", "response", "ground_truth"}
        optional = {"prior_context", "grounding_context", "request_time"}

        missing = required - set(row.keys())
        if missing:
            raise ValueError(f"CSV is missing required columns: {missing}")

        def get(col: str) -> Optional[str]:
            val = row.get(col)
            if val is None or (isinstance(val, float) and pd.isna(val)):
                return None
            val = str(val).strip()
            return val if val else None

        extra = {k: v for k, v in row.items() if k not in required | optional}

        return cls(
            utterance=str(row["utterance"]),
            response=str(row["response"]),
            ground_truth=str(row["ground_truth"]),
            prior_context=get("prior_context"),
            grounding_context=get("grounding_context"),
            request_time=get("request_time"),
            _extra=extra,
        )


@dataclass
class JudgeOutput:
    """Scores and verdict for one evaluated response."""
    # Binary scores (0 or 1)
    relevant: int
    correct_and_complete: int
    factual: int
    clear: int

    # Reasoning strings (one per axis)
    relevant_reasoning: str
    correct_and_complete_reasoning: str
    factual_reasoning: str
    clear_reasoning: str

    # Verdict
    rubric_total: int    # sum of verdict dims: relevant + correct_and_complete + clear (max 3)
    verdict: str         # "PASS" or "FAIL"
    justification: str   # brief overall summary from the judge

    # Error flag (set when the API call or JSON parse failed)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("error", None)
        if self.error:
            d["error"] = self.error
        return d

    @classmethod
    def error_row(cls, message: str) -> "JudgeOutput":
        """Return a blank output row flagged with an error message."""
        return cls(
            relevant=-1, correct_and_complete=-1, factual=-1, clear=-1,
            relevant_reasoning="", correct_and_complete_reasoning="",
            factual_reasoning="", clear_reasoning="",
            rubric_total=-1, verdict="ERROR", justification="",
            error=message,
        )

    # Ordered output column names (appended to input CSV)
    OUTPUT_COLUMNS = [
        "relevant", "relevant_reasoning",
        "correct_and_complete", "correct_and_complete_reasoning",
        "factual", "factual_reasoning",
        "clear", "clear_reasoning",
        "rubric_total", "verdict", "justification", "error",
    ]
