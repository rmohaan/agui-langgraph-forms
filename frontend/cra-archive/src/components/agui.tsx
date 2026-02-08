import { useCoAgent } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";

export const AgentUI = () => {
  const { state, nodeName, running } = useCoAgent({  name: "0" });

  console.log("Current state:", state);
  console.log("Is agent running?", running);
  console.log("Current node name:", nodeName);

  return (
    <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
      <div style={{ flex: 1, border: '1px solid #ccc', padding: '20px' }}>
        <h3>Llama Output</h3>
        {running && <p>Processing...</p>}
        {state.summary_data && <p><strong>Summary:</strong> {state.summary_data}</p>}
        {state.final_count && <p><strong>Word Count:</strong> {state.final_count}</p>}
      </div>
      <div style={{ width: '400px', height: '600px' }}>
        <CopilotChat 
          instructions="Greet the user"
          labels={{
            title: "Llama Summarizer",
            initial: "Hi! Send me some text to summarize.",
          }}
        />
      </div>
    </div>
  );
};