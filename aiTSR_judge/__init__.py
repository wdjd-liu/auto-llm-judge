"""
aiTSR v3.1 — LLM-as-a-Judge
Rubric scoring of Meta AI (Ray-Ban Meta glasses) responses on 4 binary axes.
"""
__version__ = "0.1.0"

from .judge import AiTSRJudge
from .schemas import JudgeInput, JudgeOutput

__all__ = ["AiTSRJudge", "JudgeInput", "JudgeOutput"]
