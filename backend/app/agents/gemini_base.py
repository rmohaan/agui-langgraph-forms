from __future__ import annotations

import os
from typing import Optional

from pydantic_ai import Agent


def get_gemini_model_name() -> str:
    return os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-preview-04-17")


def get_vertex_region() -> str:
    return os.environ.get("VERTEX_REGION") or os.environ.get("GOOGLE_CLOUD_REGION") or "asia-south1"


def get_vertex_project_id() -> str | None:
    return (
        os.environ.get("VERTEX_PROJECT")
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("GOOGLE_PROJECT_ID")
    )


def get_gemini_agent(instructions: str, output_type=None) -> Optional[Agent]:
    try:
        from pydantic_ai.models.gemini import GeminiModel
        from pydantic_ai.providers.google_vertex import GoogleVertexProvider
    except ImportError:
        return None

    provider = GoogleVertexProvider(
        project_id=get_vertex_project_id(),
        region=get_vertex_region(),
    )
    model = GeminiModel(get_gemini_model_name(), provider=provider)

    return Agent(
        model,
        instructions=instructions,
        output_type=output_type,
        model_settings={"temperature": 0.2},
        retries=2,
        output_retries=2,
    )
