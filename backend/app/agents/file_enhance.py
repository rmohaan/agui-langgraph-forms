from __future__ import annotations

from typing import Optional

from pydantic_ai import Agent

from ..schemas.state import EnhanceOutput
from .gemini_base import get_gemini_agent


ENHANCE_INSTRUCTIONS = (
    "You are Agent 2: Image enhancement. "
    "Given the same document base64 and quality assessment, describe enhancement steps (deskew, denoise, contrast, "
    "binarization). If you can provide an enhanced representation, return a base64-encoded image or PDF; otherwise, "
    "return instructions only."
)


def get_enhance_agent() -> Optional[Agent]:
    return get_gemini_agent(ENHANCE_INSTRUCTIONS, output_type=EnhanceOutput)
