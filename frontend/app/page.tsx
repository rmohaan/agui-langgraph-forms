"use client";

import { CopilotKit, useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useEffect, useMemo, useRef, useState } from "react";

function AgentUI() {
  const { state, running, run, nodeName } = useCoAgent({
    name: "0",
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
    <div style={{ padding: 24, display: "flex", gap: 24 }}>
      <div
        style={{
          flex: 1,
          border: "1px solid var(--border)",
          borderRadius: 12,
          background: "var(--panel)",
          padding: 16,
        }}
      >
        <h2 style={{ marginTop: 0 }}>Llama Output</h2>
        <p>
          <strong>Status:</strong> {statusWord}
        </p>
        {summaryText && (
          <p>
            <strong>Summary:</strong> {summaryText}
          </p>
        )}
        {wordCount !== null && wordCount !== undefined && (
          <p>
            <strong>Word Count:</strong> {wordCount}
          </p>
        )}
      </div>

      <div style={{ width: 400, height: 600 }}>
        <CopilotChat
          instructions="Send me text to summarize"
          onSubmitMessage={() => {
            lastNodeRef.current = null;
            applyStatus("Processing");
          }}
          labels={{
            title: "Llama Summarizer",
            initial: "Hi! Paste some text and I’ll summarize it.",
          }}
        />
      </div>
    </div>
  );
}

export default function Page() {
  return (
    <CopilotKit runtimeUrl="/api/copilotkit" agent="0">
      <AgentUI />
    </CopilotKit>
  );
}
