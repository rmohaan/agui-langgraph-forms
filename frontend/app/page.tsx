"use client";

import { CopilotKit, useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useEffect, useMemo, useRef, useState } from "react";

function AgentUI() {
  const { state, running, run, nodeName } = useCoAgent({
    name: "ag-ui-langgraph",
    initialState: {
      messages: [],
      summary_data: null,
      final_count: null,
      llm_status: "Idle",
    },
  });

  const summaryText =
    state?.summary_data && typeof state.summary_data === "object"
      ? state.summary_data.summary
      : state?.summary_data;

  const wordCount =
    state?.final_count && typeof state.final_count === "object"
      ? state.final_count.word_count
      : state?.final_count;

  const [statusWord, setStatusWord] = useState<string>("Idle");
  const lastStatusAtRef = useRef<number>(0);
  const pendingStatusRef = useRef<NodeJS.Timeout | null>(null);
  const lastNodeRef = useRef<string | null>(null);

  console.log("Current state:", state, "Current node name:", nodeName, "Is agent running?", running, "Status word:", statusWord);

  const mappedNodeStatus = useMemo(() => {
    if (nodeName === "summarizer") return "Summarizing";
    if (nodeName === "counter") return "Counting";
    return "";
  }, [nodeName]);

  const applyStatus = (next: string) => {
    const now = Date.now();
    const minVisibleMs = 600;
    const elapsed = now - lastStatusAtRef.current;

    if (pendingStatusRef.current) {
      clearTimeout(pendingStatusRef.current);
      pendingStatusRef.current = null;
    }

    if (elapsed >= minVisibleMs) {
      setStatusWord(next);
      lastStatusAtRef.current = now;
    } else {
      pendingStatusRef.current = setTimeout(() => {
        setStatusWord(next);
        lastStatusAtRef.current = Date.now();
      }, minVisibleMs - elapsed);
    }
  };

  useEffect(() => {
    const lastNode = lastNodeRef.current;
    lastNodeRef.current = nodeName ?? null;

    if (typeof state?.llm_status === "string" && state.llm_status.trim()) {
      applyStatus(state.llm_status);
      return;
    }

    if (mappedNodeStatus) {
      applyStatus(mappedNodeStatus);
      return;
    }

    if (!running && state?.final_count) {
      applyStatus("Completed");
      return;
    }

    if (running) {
      // If we just left a node, show Thinking between stages.
      if (lastNode && !nodeName) {
        applyStatus("Thinking");
        return;
      }
      applyStatus("Thinking");
      return;
    }

    applyStatus("Idle");
  }, [mappedNodeStatus, nodeName, running, state?.final_count, state?.llm_status]);

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-badge">AG-UI + LangGraph</div>
        <h1 className="hero-title">Live Summaries, Real-Time Signals</h1>
        <p className="hero-subtitle">
          Paste a paragraph and watch the agent summarize and count words with streaming status updates.
        </p>
      </header>

      <main className="grid">
        <section className="panel status-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Agent Output</p>
              <h2 className="panel-title">AG‑UI LangGraph</h2>
            </div>
            <span className={`status-pill status-${statusWord.toLowerCase()}`}>
              {statusWord}
            </span>
          </div>

          <div className="summary-card">
            <p className="label">Summary</p>
            <p className={`summary-text ${summaryText ? "" : "summary-empty"}`}>
              {summaryText || "Awaiting summary..."}
            </p>
          </div>

          <div className="metrics">
            <div className="metric">
              <p className="metric-label">Word Count</p>
              <p className="metric-value">{wordCount ?? "—"}</p>
            </div>
            <div className="metric">
              <p className="metric-label">Active Node</p>
              <p className="metric-value">{nodeName || "idle"}</p>
            </div>
          </div>
        </section>

        <section className="panel chat-panel">
          <div className="panel-header">
            <div>
              <p className="eyebrow">Input</p>
              <h2 className="panel-title">Paste Text</h2>
            </div>
          </div>
          <div className="chat-shell">
            <CopilotChat
              instructions="Send me text to summarize"
              onSubmitMessage={() => {
                lastNodeRef.current = null;
                applyStatus("Processing");
              }}
              labels={{
                title: "AG‑UI LangGraph",
                initial: "Hi! Paste some text and I’ll summarize it.",
              }}
            />
          </div>
        </section>
      </main>
    </div>
  );
}

export default function Page() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="ag-ui-langgraph">
      <AgentUI />
    </CopilotKit>
  );
}
