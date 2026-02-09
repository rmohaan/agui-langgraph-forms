from pydantic import BaseModel, Field
from typing import TypedDict, Optional, List, Dict, Any

class SummaryOutput(BaseModel):
    summary: str = Field(description="The summarized version of the text")
    key_points: List[str] = Field(description="Main topics")

class CountOutput(BaseModel):
    word_count: int = Field(description="Number of words")

class FileReference(BaseModel):
    file_id: str = Field(description="Uploaded file id")
    filename: str = Field(description="Original filename")
    content_type: str = Field(description="MIME type")
    size: int = Field(description="File size in bytes")

class FileQualityOutput(BaseModel):
    blur_score: float = Field(description="Variance of Laplacian blur score")
    skew_angle: float = Field(description="Estimated skew angle in degrees")
    lighting_variance: float = Field(description="Variance of grayscale intensity")
    issues: List[str] = Field(description="Quality issues detected")
    image_count: int = Field(description="Number of images/pages processed")

class PreprocessOutput(BaseModel):
    total_boxes: int = Field(description="Total detected bounding boxes")
    boxes_per_page: List[int] = Field(description="Bounding boxes per page")

class EnhanceOutput(BaseModel):
    instructions: str = Field(description="Enhancement guidance such as deskew/denoise steps")
    enhanced_base64: Optional[str] = Field(description="Optional enhanced document encoded in base64")

class ExtractedDataOutput(BaseModel):
    raw_text: str = Field(description="Extracted handwriting text")
    page_count: int = Field(description="Pages processed")

class GroundedOutput(BaseModel):
    normalized_text: str = Field(description="Grounded/normalized text")
    entities: List[Dict[str, Any]] = Field(description="Extracted structured entities")
    notes: Optional[str] = Field(description="Grounding notes")

class AgentState(TypedDict):
    input_text: str
    messages: Optional[List[Dict[str, Any]]]
    summary_data: Optional[Dict[str, Any]]
    translated_data: Optional[Dict[str, Any]]
    final_count: Optional[Dict[str, Any]]
    llm_status: Optional[str]
    file_ref: Optional[Dict[str, Any]]
    file_quality: Optional[Dict[str, Any]]
    enhanced_files: Optional[List[str]]
    enhanced_data: Optional[Dict[str, Any]]
    preprocess_data: Optional[Dict[str, Any]]
    extracted_data: Optional[Dict[str, Any]]
    grounded_data: Optional[Dict[str, Any]]
    file_errors: Optional[List[str]]
