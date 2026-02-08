import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.callbacks import adispatch_custom_event
from langchain_core.runnables import RunnableConfig
from ag_ui_langgraph.types import CustomEventNames

from ..schemas.state import AgentState
from ..agents.summarizer import summarizer_agent
from ..agents.counter import counter_agent

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
    await asyncio.sleep(0.5)

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

workflow = StateGraph(AgentState)
workflow.add_node("summarizer", summarize_node)
workflow.add_node("counter", count_node)
workflow.add_edge(START, "summarizer")
workflow.add_edge("summarizer", "counter")
workflow.add_edge("counter", END)

memory = MemorySaver()
graph = workflow.compile(checkpointer=memory)
