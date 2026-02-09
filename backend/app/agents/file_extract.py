from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent

from ..schemas.state import ExtractedDataOutput
from .gemini_base import get_gemini_agent


EXTRACT_INSTRUCTIONS = (
    "You are Agent 4: Handwriting extraction. "
    "Given the document base64 and any preprocessing hints, extract the handwritten text. "
    "Return the raw extracted text and the page count."
)


def get_extract_agent() -> Optional[Agent]:
    return get_gemini_agent(EXTRACT_INSTRUCTIONS, output_type=ExtractedDataOutput)
