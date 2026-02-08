import { CopilotKit, useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

export const AgentUI = () => {
  const { state, running, run } = useCoAgent({
    name: "0",   // must match backend agent name
    initialState: {
      messages: [],
      summary_data: null,
      final_count: null,
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

  return (
    <div style={{ display: "flex", gap: "20px", padding: "20px" }}>
      <div style={{ flex: 1, border: "1px solid #ccc", padding: "20px" }}>
        <h3>Llama Output</h3>
        {running && <p>Processing...</p>}
        {summaryText && <p><strong>Summary:</strong> {summaryText}</p>}
        {wordCount && <p><strong>Word Count:</strong> {wordCount}</p>}
      </div>

      <button onClick={() => run({ state: { input_text: "Test input" } })}>
        Run Agent
      </button>

      <div style={{ width: "400px", height: "600px" }}>
        <CopilotChat
          instructions="Send me text to summarize"
          labels={{
            title: "Llama Summarizer",
            initial: "Hi! Paste some text and I’ll summarize it.",
          }}
        />
      </div>
    </div>
  );
};

export default function App() {
  return (
    <CopilotKit
      runtimeUrl={
        process.env.REACT_APP_COPILOTKIT_RUNTIME_URL ??
        "http://localhost:4000/copilotkit"
      }
      agent="0"
    >
        <AgentUI />
    </CopilotKit>
  );
}
