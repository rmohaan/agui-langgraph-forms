from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent

from ..schemas.state import GroundedOutput
from .gemini_base import get_gemini_agent


GROUNDING_INSTRUCTIONS = (
    "You are Agent 5: Ground the extracted handwritten data. "
    "Normalize and structure the extracted text, returning concise normalized text and key-value entities."
)


def get_grounding_agent() -> Optional[Agent]:
    return get_gemini_agent(GROUNDING_INSTRUCTIONS, output_type=GroundedOutput)
