import http from "node:http";
import {
  CopilotRuntime,
  copilotRuntimeNodeHttpEndpoint,
  ExperimentalEmptyAdapter,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const PORT = Number(process.env.COPILOTKIT_RUNTIME_PORT ?? 4000);
const AGUI_ENDPOINT =
  process.env.AGUI_ENDPOINT ?? "http://localhost:8000/agui";

const runtime = new CopilotRuntime({
  agents: {
    "0": new LangGraphHttpAgent({
      url: AGUI_ENDPOINT,
      agentId: "0",
      description: "AG-UI LangGraph agent",
    }),
  },
});

const handler = copilotRuntimeNodeHttpEndpoint({
  runtime,
  serviceAdapter: new ExperimentalEmptyAdapter(),
  endpoint: "/copilotkit",
  cors: {
    origin: [
      "http://localhost:3000",
      "http://127.0.0.1:3000",
    ],
    credentials: true,
  },
});

const server = http.createServer((req, res) => handler(req, res));

server.listen(PORT, () => {
  // eslint-disable-next-line no-console
  console.log(
    `CopilotKit runtime server listening on http://localhost:${PORT}/copilotkit (AGUI: ${AGUI_ENDPOINT})`
  );
});
