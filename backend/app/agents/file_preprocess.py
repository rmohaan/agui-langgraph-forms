from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent

from ..schemas.state import PreprocessOutput
from .gemini_base import get_gemini_agent


PREPROCESS_INSTRUCTIONS = (
    "You are Agent 3: Preprocess for handwriting bounding boxes. "
    "Given the document base64 and any enhancement guidance, identify regions likely containing handwritten text. "
    "Return a count of total boxes and counts per page. Use best-effort estimation if exact detection is not possible."
)


def get_preprocess_agent() -> Optional[Agent]:
    return get_gemini_agent(PREPROCESS_INSTRUCTIONS, output_type=PreprocessOutput)
