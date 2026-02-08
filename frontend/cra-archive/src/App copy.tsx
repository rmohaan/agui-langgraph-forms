import { CopilotKit } from "@copilotkit/react-core";
import { CopilotSidebar } from "@copilotkit/react-ui";
import { AgentUI } from "./components/agui.tsx";
import "@copilotkit/react-ui/styles.css";

function App() {
  return (
    <CopilotKit 
        runtimeUrl="http://localhost:8000/copilotkit" 
        agent="0"
    >

      {/* <CopilotSidebar
        instructions="I am an assistant powered by Llama3.1. I can summarize text and provide word counts using a multi-agent workflow."
        defaultOpen={true}
        clickOutsideToClose={true}
      > */}
        {/* Your custom component where the state from useCoAgent is displayed */}
        <AgentUI />
      {/* </CopilotSidebar> */}
    </CopilotKit>

  );
}

export default App;