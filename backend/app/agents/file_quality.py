from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent

from ..schemas.state import FileQualityOutput
from .gemini_base import get_gemini_agent


QUALITY_INSTRUCTIONS = (
    "You are Agent 1: Image quality assessment. "
    "Given a document (image/tiff/pdf) encoded as base64 and metadata, assess skewness, blur, and lighting variance. "
    "Return numeric scores and a list of issues. If unable to compute exact metrics, estimate based on visible cues and "
    "note assumptions in issues."
)


def get_quality_agent() -> Optional[Agent]:
    return get_gemini_agent(QUALITY_INSTRUCTIONS, output_type=FileQualityOutput)
