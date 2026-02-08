from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List, Dict, Any

class SummaryOutput(BaseModel):
    summary: str = Field(description="The summarized version of the text")
    key_points: List[str] = Field(description="Main topics")

class CountOutput(BaseModel):
    word_count: int = Field(description="Number of words")

class AgentState(TypedDict):
    input_text: str
    messages: Optional[List[Dict[str, Any]]]
    summary_data: Optional[Dict[str, Any]]
    final_count: Optional[Dict[str, Any]]
    llm_status: Optional[str]
