"use client";

import { CopilotKit, useCoAgent, useCopilotChat } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { useEffect, useMemo, useRef, useState } from "react";
import { MessageRole, TextMessage } from "@copilotkit/runtime-client-gql";
import { CustomUserMessage } from "./components/CustomUserMessage";

type SummaryData = {
  summary: string;
  key_points: string[];
};

type TranslatedData = {
  translated_text: string;
};

type FinalCount = {
  word_count: number;
};

type FileQuality = {
  blur_score: number;
  skew_angle: number;
  lighting_variance: number;
  issues: string[];
  image_count: number;
};

type PreprocessData = {
  total_boxes: number;
  boxes_per_page: number[];
};

type ExtractedData = {
  raw_text: string;
  page_count: number;
};

type GroundedData = {
  normalized_text: string;
  entities: Array<Record<string, unknown>>;
  notes?: string | null;
};

type AgentState = {
  messages: Array<Record<string, unknown>>;
  summary_data: SummaryData | string | null;
  translated_data: TranslatedData | string | null;
  final_count: FinalCount | number | null;
  llm_status: string;
  file_ref?: Record<string, unknown> | null;
  file_quality?: FileQuality | null;
  preprocess_data?: PreprocessData | null;
  extracted_data?: ExtractedData | null;
  grounded_data?: GroundedData | null;
  file_errors?: string[] | null;
};

function AgentUI() {
  const { appendMessage } = useCopilotChat();
  const { state, running, nodeName } = useCoAgent<AgentState>({
    name: "ag-ui-langgraph",
    initialState: {
      messages: [],
      summary_data: null,
      translated_data: null,
      final_count: null,
      llm_status: "Idle",
      file_ref: null,
      file_quality: null,
      preprocess_data: null,
      extracted_data: null,
      grounded_data: null,
      file_errors: null,
    },
  });

  const summaryText =
    state?.summary_data && typeof state.summary_data === "object"
      ? state.summary_data.summary
      : typeof state?.summary_data === "string"
        ? state.summary_data
        : null;

  const translatedText =
    state?.translated_data && typeof state.translated_data === "object"
      ? state.translated_data.translated_text
      : typeof state?.translated_data === "string"
        ? state.translated_data
        : null;

  const wordCount =
    state?.final_count && typeof state.final_count === "object"
      ? state.final_count.word_count
      : typeof state?.final_count === "number"
        ? state.final_count
        : null;

  const fileQuality = state?.file_quality ?? null;
  const preprocessData = state?.preprocess_data ?? null;
  const extractedData = state?.extracted_data ?? null;
  const groundedData = state?.grounded_data ?? null;
  const fileErrors = state?.file_errors ?? null;

  const [statusWord, setStatusWord] = useState<string>("Idle");
  const lastStatusAtRef = useRef<number>(0);
  const pendingStatusRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastNodeRef = useRef<string | null>(null);

  console.log("Current state:", state, "Current node name:", nodeName, "Is agent running?", running, "Status word:", statusWord);

  const mappedNodeStatus = useMemo(() => {
    if (nodeName === "summarizer") return "Summarizing";
    if (nodeName === "translate") return "Translating";
    if (nodeName === "counter") return "Counting";
    if (nodeName === "file_quality") return "Assessing";
    if (nodeName === "file_enhance") return "Enhancing";
    if (nodeName === "file_preprocess") return "Preprocessing";
    if (nodeName === "file_extract") return "Extracting";
    if (nodeName === "file_ground") return "Grounding";
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

  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [lastUploadLabel, setLastUploadLabel] = useState<string | null>(null);
  const uploadInputRef = useRef<HTMLInputElement | null>(null);

  const handleUpload = async (file: File) => {
    setUploadError(null);
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      const response = await fetch("/api/upload", { method: "POST", body: formData });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || "Upload failed");
      }
      const payload = await response.json();
      const messagePayload = {
        file_id: payload.file_id,
        filename: payload.filename,
        content_type: payload.content_type,
        size: payload.size,
      };
      const content = `FILE_UPLOAD::${JSON.stringify(messagePayload)}`;
      await appendMessage(
        new TextMessage({
          role: MessageRole.User,
          content,
        }),
      );
      setLastUploadLabel(`${payload.filename} (${payload.content_type})`);
      applyStatus("Processing");
    } catch (error) {
      setUploadError(error instanceof Error ? error.message : "Upload failed");
    } finally {
      setUploading(false);
      if (uploadInputRef.current) {
        uploadInputRef.current.value = "";
      }
    }
  };

  const handleFileChange = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    await handleUpload(file);
  };

  return (
    <div className="page">
      <header className="hero">
        <div className="hero-badge">AG-UI + LangGraph</div>
        <h1 className="hero-title">Live Summaries, Real-Time Signals</h1>
        <p className="hero-subtitle">
          Paste text for summaries or upload a document to extract handwritten data with streaming status updates.
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

          <div className="summary-card">
            <p className="label">Translation (Hindi)</p>
            <p className={`summary-text ${translatedText ? "" : "summary-empty"}`}>
              {translatedText || "Awaiting translation..."}
            </p>
          </div>

          {fileErrors && fileErrors.length > 0 && (
            <div className="summary-card summary-error">
              <p className="label">File Processing Issues</p>
              <p className="summary-text summary-empty">{fileErrors.join(" | ")}</p>
            </div>
          )}

          <div className="summary-card">
            <p className="label">File Quality</p>
            <p className={`summary-text ${fileQuality ? "" : "summary-empty"}`}>
              {fileQuality
                ? `Blur: ${fileQuality.blur_score.toFixed(1)}, Skew: ${fileQuality.skew_angle.toFixed(
                    2,
                  )}°, Lighting: ${fileQuality.lighting_variance.toFixed(1)}`
                : "Awaiting file quality..."}
            </p>
            {fileQuality && fileQuality.issues.length > 0 && (
              <p className="summary-subtext">Issues: {fileQuality.issues.join(", ")}</p>
            )}
          </div>

          <div className="summary-card">
            <p className="label">Handwriting Extraction</p>
            <p className={`summary-text ${extractedData?.raw_text ? "" : "summary-empty"}`}>
              {extractedData?.raw_text || "Awaiting extraction..."}
            </p>
            {preprocessData && (
              <p className="summary-subtext">
                Boxes: {preprocessData.total_boxes} | Pages: {extractedData?.page_count ?? 0}
              </p>
            )}
          </div>

          <div className="summary-card">
            <p className="label">Grounded Output</p>
            <p className={`summary-text ${groundedData?.normalized_text ? "" : "summary-empty"}`}>
              {groundedData?.normalized_text || "Awaiting grounding..."}
            </p>
            {groundedData?.notes && (
              <p className="summary-subtext">{groundedData.notes}</p>
            )}
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
              <h2 className="panel-title">Paste Text or Upload</h2>
            </div>
            <div className="upload-controls">
              <label className={`upload-button ${uploading ? "uploading" : ""}`}>
                {uploading ? "Uploading..." : "Upload file"}
                <input
                  ref={uploadInputRef}
                  type="file"
                  accept="image/*,application/pdf,image/tiff,.tif,.tiff"
                  onChange={handleFileChange}
                  disabled={uploading}
                />
              </label>
              <span className="upload-meta">
                {uploadError
                  ? uploadError
                  : lastUploadLabel ?? "PNG, JPG, TIFF, or PDF"}
              </span>
            </div>
          </div>
          <div className="chat-shell">
            <CopilotChat
              instructions="Send me text to summarize or upload a document to extract handwriting."
              onSubmitMessage={() => {
                lastNodeRef.current = null;
                applyStatus("Processing");
              }}
              labels={{
                title: "AG‑UI LangGraph",
                initial: "Hi! Paste text or upload a document to get started.",
              }}
              UserMessage={CustomUserMessage}
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
