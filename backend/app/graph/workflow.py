import asyncio
import base64
import json
from typing import Optional
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from ag_ui_langgraph.types import CustomEventNames

from ..schemas.state import AgentState
from ..agents.summarizer import summarizer_agent
from ..agents.translator import translator_agent
from ..agents.counter import counter_agent
from ..agents.grounder import get_grounding_agent
from ..agents.file_quality import get_quality_agent
from ..agents.file_enhance import get_enhance_agent
from ..agents.file_preprocess import get_preprocess_agent
from ..agents.file_extract import get_extract_agent
from ..file_store import get_upload

def _get_input_text(state: AgentState) -> str:
    input_text = state.get("input_text")
    if isinstance(input_text, str) and input_text.strip():
        return input_text

    messages = state.get("messages") if isinstance(state, dict) else None
    if isinstance(messages, list):
        for message in reversed(messages):
            if isinstance(message, dict):
                role = message.get("role") or message.get("type")
                if role in {"user", "human"}:
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content
            else:
                role = getattr(message, "role", None) or getattr(message, "type", None)
                if role in {"user", "human"}:
                    content = getattr(message, "content", None)
                    if isinstance(content, str) and content.strip():
                        return content
    return ""

def _parse_file_upload_message(text: str) -> Optional[dict]:
    prefix = "FILE_UPLOAD::"
    if not isinstance(text, str) or not text.startswith(prefix):
        return None
    payload = text[len(prefix):].strip()
    if not payload:
        return None
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    if "file_id" not in data:
        return None
    return data

def _get_file_ref(state: AgentState) -> Optional[dict]:
    input_text = _get_input_text(state)
    return _parse_file_upload_message(input_text)

def _model_dump(value):
    if value is None:
        return None
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return value

def _clean_summary_text(text: str) -> str:
    cleaned = text.strip()
    lowered = cleaned.lower()
    if lowered.startswith("here is a summary"):
        if "\n\n" in cleaned:
            cleaned = cleaned.split("\n\n", 1)[1].strip()
        elif ":" in cleaned:
            cleaned = cleaned.split(":", 1)[1].strip()
    if lowered.startswith("summary:"):
        cleaned = cleaned.split(":", 1)[1].strip()
    return " ".join(cleaned.split())

async def _emit_status(state: AgentState, config: RunnableConfig | None, status: str) -> None:
    if not config:
        return
    if isinstance(state, dict):
        state["llm_status"] = status
    payload = dict(state) if isinstance(state, dict) else {}
    payload["llm_status"] = status
    print(f"Emitting status update: {status}")
    await adispatch_custom_event(
        CustomEventNames.ManuallyEmitState.value,
        payload,
        config=config,
    )
    print(f"Status update emitted: {status}")
    # Give the event loop a moment so the stream can flush intermediate status updates.
    await asyncio.sleep(2.5)

def _load_file_payload(record) -> dict:
    data = record.path.read_bytes()
    return {
        "file_id": record.file_id,
        "filename": record.filename,
        "content_type": record.content_type,
        "size": record.size,
        "base64": base64.b64encode(data).decode("utf-8"),
    }

async def file_quality_node(state: AgentState, config: RunnableConfig | None = None):
    file_ref = _get_file_ref(state)
    if not file_ref:
        return {"file_errors": ["No file reference found"], "llm_status": "Completed"}

    record = get_upload(file_ref["file_id"])
    if not record:
        return {"file_errors": ["Uploaded file not found"], "llm_status": "Completed"}

    await _emit_status(state, config, "Assessing")
    quality_agent = get_quality_agent()
    if not quality_agent:
        return {"file_errors": ["Vertex AI credentials not configured for quality assessment"], "llm_status": "Completed"}

    file_payload = _load_file_payload(record)
    try:
        res = await quality_agent.run(json.dumps(file_payload))
        quality_data = res.data if hasattr(res, "data") else res
    except Exception as exc:  # pylint: disable=broad-except
        return {"file_errors": [f"Quality agent failed: {exc}"], "llm_status": "Completed"}

    if hasattr(quality_data, "model_dump"):
        quality_payload = quality_data.model_dump()
    elif isinstance(quality_data, dict):
        quality_payload = quality_data
    else:
        quality_payload = {
            "blur_score": 0.0,
            "skew_angle": 0.0,
            "lighting_variance": 0.0,
            "issues": ["Unable to parse quality output"],
            "image_count": 0,
        }

    state["file_ref"] = file_ref
    state["file_quality"] = quality_payload
    await _emit_status(state, config, "Enhancing")
    return {"file_ref": file_ref, "file_quality": quality_payload, "llm_status": "Enhancing"}

async def file_enhance_node(state: AgentState, config: RunnableConfig | None = None):
    file_ref = state.get("file_ref") or _get_file_ref(state)
    if not file_ref:
        return {"file_errors": ["No file reference found"], "llm_status": "Completed"}

    record = get_upload(file_ref["file_id"])
    if not record:
        return {"file_errors": ["Uploaded file not found"], "llm_status": "Completed"}

    enhance_agent = get_enhance_agent()
    if not enhance_agent:
        return {"file_errors": ["Vertex AI credentials not configured for enhancement"], "llm_status": "Completed"}

    file_payload = _load_file_payload(record)
    quality_payload = state.get("file_quality")
    request_payload = {
        "file": file_payload,
        "quality": quality_payload,
    }
    try:
        res = await enhance_agent.run(json.dumps(request_payload))
        enhance_data = res.data if hasattr(res, "data") else res
    except Exception as exc:  # pylint: disable=broad-except
        return {"file_errors": [f"Enhancement agent failed: {exc}"], "llm_status": "Completed"}

    if hasattr(enhance_data, "model_dump"):
        enhance_payload = enhance_data.model_dump()
    elif isinstance(enhance_data, dict):
        enhance_payload = enhance_data
    else:
        enhance_payload = {"instructions": "Unable to parse enhancement output", "enhanced_base64": None}

    state["enhanced_data"] = enhance_payload
    await _emit_status(state, config, "Preprocessing")
    return {"enhanced_data": enhance_payload, "llm_status": "Preprocessing"}

async def file_preprocess_node(state: AgentState, config: RunnableConfig | None = None):
    file_ref = state.get("file_ref") or _get_file_ref(state)
    if not file_ref:
        return {"file_errors": ["No file reference found"], "llm_status": "Completed"}

    record = get_upload(file_ref["file_id"])
    if not record:
        return {"file_errors": ["Uploaded file not found"], "llm_status": "Completed"}

    preprocess_agent = get_preprocess_agent()
    if not preprocess_agent:
        return {"file_errors": ["Vertex AI credentials not configured for preprocessing"], "llm_status": "Completed"}

    enhance_payload = state.get("enhanced_data")
    request_payload = {
        "file": _load_file_payload(record),
        "enhancement": enhance_payload,
    }
    try:
        res = await preprocess_agent.run(json.dumps(request_payload))
        preprocess_data = res.data if hasattr(res, "data") else res
    except Exception as exc:  # pylint: disable=broad-except
        return {"file_errors": [f"Preprocess agent failed: {exc}"], "llm_status": "Completed"}

    if hasattr(preprocess_data, "model_dump"):
        preprocess_payload = preprocess_data.model_dump()
    elif isinstance(preprocess_data, dict):
        preprocess_payload = preprocess_data
    else:
        preprocess_payload = {"total_boxes": 0, "boxes_per_page": []}

    state["preprocess_data"] = preprocess_payload
    await _emit_status(state, config, "Extracting")
    return {"preprocess_data": preprocess_payload, "llm_status": "Extracting"}

async def file_extract_node(state: AgentState, config: RunnableConfig | None = None):
    file_ref = state.get("file_ref") or _get_file_ref(state)
    if not file_ref:
        return {"file_errors": ["No file reference found"], "llm_status": "Completed"}

    record = get_upload(file_ref["file_id"])
    if not record:
        return {"file_errors": ["Uploaded file not found"], "llm_status": "Completed"}

    extract_agent = get_extract_agent()
    if not extract_agent:
        return {"file_errors": ["Vertex AI credentials not configured for extraction"], "llm_status": "Completed"}

    request_payload = {
        "file": _load_file_payload(record),
        "preprocess": state.get("preprocess_data"),
        "enhancement": state.get("enhanced_data"),
    }
    try:
        res = await extract_agent.run(json.dumps(request_payload))
        extract_data = res.data if hasattr(res, "data") else res
    except Exception as exc:  # pylint: disable=broad-except
        return {"file_errors": [f"Extract agent failed: {exc}"], "llm_status": "Completed"}

    if hasattr(extract_data, "model_dump"):
        extract_payload = extract_data.model_dump()
    elif isinstance(extract_data, dict):
        extract_payload = extract_data
    else:
        extract_payload = {"raw_text": str(extract_data), "page_count": 0}

    state["extracted_data"] = extract_payload
    await _emit_status(state, config, "Grounding")
    return {"extracted_data": extract_payload, "llm_status": "Grounding"}

async def file_ground_node(state: AgentState, config: RunnableConfig | None = None):
    extracted = state.get("extracted_data") or {}
    raw_text = ""
    if isinstance(extracted, dict):
        raw_text = extracted.get("raw_text") or ""

    grounding_agent = get_grounding_agent()
    if not grounding_agent:
        grounded_payload = {
            "normalized_text": raw_text,
            "entities": [],
            "notes": "Gemini 2.5 Flash not configured; returning raw extraction.",
        }
        state["grounded_data"] = grounded_payload
        await _emit_status(state, config, "Completed")
        return {"grounded_data": grounded_payload, "llm_status": "Completed"}

    try:
        res = await grounding_agent.run(raw_text or "")
        if hasattr(res, "data"):
            grounded = res.data
        elif hasattr(res, "output"):
            grounded = res.output
        else:
            grounded = res
    except Exception as exc:  # pylint: disable=broad-except
        grounded = {
            "normalized_text": raw_text,
            "entities": [],
            "notes": f"Grounding failed: {exc}",
        }

    if hasattr(grounded, "model_dump"):
        grounded_payload = grounded.model_dump()
    elif isinstance(grounded, dict):
        grounded_payload = grounded
    else:
        grounded_payload = {"normalized_text": str(grounded), "entities": [], "notes": None}

    state["grounded_data"] = grounded_payload
    await _emit_status(state, config, "Completed")
    return {"grounded_data": grounded_payload, "llm_status": "Completed"}

def _route_input(state: AgentState) -> str:
    if _get_file_ref(state):
        return "file"
    return "text"

def _route_file_after_quality(state: AgentState) -> str:
    errors = state.get("file_errors") or []
    return "file_error" if errors else "file_enhance"

def _route_file_after_enhance(state: AgentState) -> str:
    errors = state.get("file_errors") or []
    return "file_error" if errors else "file_preprocess"

def _route_file_after_preprocess(state: AgentState) -> str:
    errors = state.get("file_errors") or []
    return "file_error" if errors else "file_extract"

def _route_file_after_extract(state: AgentState) -> str:
    errors = state.get("file_errors") or []
    return "file_error" if errors else "file_ground"

async def summarize_node(state: AgentState, config: RunnableConfig | None = None):
    input_text = _get_input_text(state)
    if not input_text:
        return {"summary_data": {"summary": "", "key_points": []}, "llm_status": "Completed"}
    print("Input text to summarize:", input_text)
    await _emit_status(state, config, "Processing")
    await _emit_status(state, config, "Thinking")
    await _emit_status(state, config, "Summarizing")
    try:
        res = await summarizer_agent.run(input_text)
        if hasattr(res, "data"):
            summary = res.data
        elif hasattr(res, "output"):
            summary = res.output
        else:
            summary = res
    except Exception as exc:  # pylint: disable=broad-except
        # Fallback to a naive summary to keep the graph running
        print("Summarizer failed, falling back to naive summary:", exc)
        summary = {"summary": input_text[:300], "key_points": []}
    if isinstance(summary, str):
        summary_payload = {"summary": _clean_summary_text(summary), "key_points": []}
    elif isinstance(summary, dict) and "summary" in summary:
        summary_payload = summary
    else:
        summary_payload = _model_dump(summary)
    state["summary_data"] = summary_payload
    await _emit_status(state, config, "Thinking")
    return {"summary_data": summary_payload, "llm_status": "Thinking"}

async def count_node(state: AgentState, config: RunnableConfig | None = None):
    print("Summary to count words in:", state["summary_data"])
    await _emit_status(state, config, "Counting")
    summary_data = state.get("summary_data")
    if isinstance(summary_data, dict):
        summary_text = summary_data.get("summary")
    else:
        summary_text = getattr(summary_data, "summary", None)
    input_text = _get_input_text(state)
    text_to_count = _clean_summary_text(summary_text or input_text or "")
    word_count = len([w for w in text_to_count.split() if w.strip()])
    count_payload = {"word_count": word_count}
    state["final_count"] = count_payload
    await _emit_status(state, config, "Completed")
    return {"final_count": count_payload, "llm_status": "Completed"}

async def translate_node(state: AgentState, config: RunnableConfig | None = None):
    print("Summary to translate:", state["summary_data"])
    await _emit_status(state, config, "Translating")
    summary_data = state.get("summary_data")
    if isinstance(summary_data, dict):
        summary_text = summary_data.get("summary")
    else:
        summary_text = getattr(summary_data, "summary", None)
    input_text = _get_input_text(state)
    text_to_translate = _clean_summary_text(summary_text or input_text or "")
    try:
        res = await translator_agent.run(text_to_translate)
        if hasattr(res, "data"):
            translated = res.data
        elif hasattr(res, "output"):
            translated = res.output
        else:
            translated = res
    except Exception as exc:  # pylint: disable=broad-except
        print("Translator failed, falling back to original summary:", exc)
        translated = text_to_translate

    if isinstance(translated, str):
        translated_payload = {"translated_text": _clean_summary_text(translated)}
    elif isinstance(translated, dict) and "translated_text" in translated:
        translated_payload = translated
    else:
        translated_payload = {"translated_text": _clean_summary_text(str(translated))}

    state["translated_data"] = translated_payload
    await _emit_status(state, config, "Thinking")
    return {"translated_data": translated_payload, "llm_status": "Thinking"}

workflow = StateGraph(AgentState)
workflow.add_node("file_quality", file_quality_node)
workflow.add_node("file_enhance", file_enhance_node)
workflow.add_node("file_preprocess", file_preprocess_node)
workflow.add_node("file_extract", file_extract_node)
workflow.add_node("file_ground", file_ground_node)
workflow.add_node("summarizer", summarize_node)
workflow.add_node("translate", translate_node)
workflow.add_node("counter", count_node)
workflow.add_conditional_edges(START, _route_input, {"file": "file_quality", "text": "summarizer"})
workflow.add_conditional_edges("file_quality", _route_file_after_quality, {"file_enhance": "file_enhance", "file_error": END})
workflow.add_conditional_edges("file_enhance", _route_file_after_enhance, {"file_preprocess": "file_preprocess", "file_error": END})
workflow.add_conditional_edges("file_preprocess", _route_file_after_preprocess, {"file_extract": "file_extract", "file_error": END})
workflow.add_conditional_edges("file_extract", _route_file_after_extract, {"file_ground": "file_ground", "file_error": END})
workflow.add_edge("file_ground", END)
workflow.add_edge("summarizer", "translate")
workflow.add_edge("translate", "counter")
workflow.add_edge("counter", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
