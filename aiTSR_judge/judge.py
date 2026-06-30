# aiTSR v3.1 — Rubric Judge
from __future__ import annotations
import json
import os
import re
import time
from typing import Optional

import anthropic

from .prompts import (
    RUBRIC_JUDGE_SYSTEM_PROMPT,
    RUBRIC_JUDGE_USER_PROMPT,
    RUBRIC_VERDICT_DIMENSIONS,
    RUBRIC_VERDICT_PASS_THRESHOLD,
)
from .schemas import JudgeInput, JudgeOutput


class AiTSRJudge:
    """
    Rubric judge for aiTSR v3.1.

    Scores an assistant response on 4 binary axes (Relevant, Correct & Complete,
    Factual, Clear) using Claude Opus 4 with extended thinking.
    Returns a PASS/FAIL verdict based on the 3 verdict dimensions.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4-5",
        extended_thinking: bool = True,
        thinking_budget: int = 10_000,
        max_retries: int = 3,
        retry_delay: float = 2.0,
    ):
        self.model = model
        self.extended_thinking = extended_thinking
        self.thinking_budget = thinking_budget
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY")
        )

    # ── public API ────────────────────────────────────────────────

    def score(self, inp: JudgeInput) -> JudgeOutput:
        """Score a single JudgeInput. Returns JudgeOutput (or error row on failure)."""
        user_prompt = self._build_user_prompt(inp)

        for attempt in range(1, self.max_retries + 1):
            try:
                raw_json = self._call_api(user_prompt)
                return self._parse_response(raw_json)
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                if attempt == self.max_retries:
                    return JudgeOutput.error_row(
                        f"Parse error after {self.max_retries} attempts: {e}"
                    )
                time.sleep(self.retry_delay)
            except anthropic.APIError as e:
                if attempt == self.max_retries:
                    return JudgeOutput.error_row(f"API error: {e}")
                time.sleep(self.retry_delay * attempt)

        return JudgeOutput.error_row("Unknown failure")

    def score_batch(
        self,
        inputs: list[JudgeInput],
        progress: bool = True,
    ) -> list[JudgeOutput]:
        """Score a list of JudgeInputs sequentially. Never raises — errors go to error_row."""
        outputs = []
        total = len(inputs)
        for i, inp in enumerate(inputs, 1):
            if progress:
                print(f"[{i}/{total}] Scoring row {i}…", end=" ", flush=True)
            out = self.score(inp)
            if progress:
                status = f"✓ {out.verdict}" if out.error is None else f"✗ ERROR"
                print(status)
            outputs.append(out)
        return outputs

    # ── private helpers ───────────────────────────────────────────

    def _build_user_prompt(self, inp: JudgeInput) -> str:
        """Assemble the user prompt with optional context blocks."""
        request_time_block = (
            f"[REQUEST TIME: {inp.request_time}]\n" if inp.request_time else ""
        )
        grounding_info_block = (
            f"[GROUNDING CONTEXT]\n{inp.grounding_context}\n\n"
            if inp.grounding_context
            else ""
        )
        prior_context_block = (
            f"[PRIOR CONVERSATION CONTEXT]\n{inp.prior_context}\n\n"
            if inp.prior_context
            else ""
        )
        return RUBRIC_JUDGE_USER_PROMPT.format(
            request_time_block=request_time_block,
            grounding_info_block=grounding_info_block,
            prior_context_block=prior_context_block,
            utterance=inp.utterance,
            response=inp.response,
            ground_truth=inp.ground_truth,
        )

    def _call_api(self, user_prompt: str) -> str:
        """Call Claude and return the text content block (not the thinking block)."""
        kwargs = dict(
            model=self.model,
            max_tokens=16_000,
            system=RUBRIC_JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        if self.extended_thinking:
            kwargs["thinking"] = {
                "type": "enabled",
                "budget_tokens": self.thinking_budget,
            }

        response = self.client.messages.create(**kwargs)

        # Extract the text block (skip thinking blocks)
        for block in response.content:
            if block.type == "text":
                return block.text

        raise ValueError("No text block found in Claude response")

    def _parse_response(self, text: str) -> JudgeOutput:
        """Parse Claude's JSON response into a JudgeOutput."""
        # Strip markdown code fences if present
        text = text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        data = json.loads(text)

        def get_score(key: str) -> int:
            val = data[key]
            if isinstance(val, bool):
                return int(val)
            return int(val)

        relevant             = get_score("relevant")
        correct_and_complete = get_score("correct_and_complete")
        factual              = get_score("factual")
        clear                = get_score("clear")

        # Compute verdict from the 3 verdict dimensions (factual excluded)
        scores = {
            "relevant": relevant,
            "correct_and_complete": correct_and_complete,
            "clear": clear,
        }
        rubric_total = sum(scores[d] for d in RUBRIC_VERDICT_DIMENSIONS)
        verdict = "PASS" if rubric_total >= RUBRIC_VERDICT_PASS_THRESHOLD else "FAIL"

        return JudgeOutput(
            relevant=relevant,
            correct_and_complete=correct_and_complete,
            factual=factual,
            clear=clear,
            relevant_reasoning=data.get("relevant_reasoning", ""),
            correct_and_complete_reasoning=data.get("correct_and_complete_reasoning", ""),
            factual_reasoning=data.get("factual_reasoning", ""),
            clear_reasoning=data.get("clear_reasoning", ""),
            rubric_total=rubric_total,
            verdict=verdict,
            justification=data.get("justification", ""),
        )
