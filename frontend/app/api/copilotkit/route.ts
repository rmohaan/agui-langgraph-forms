import { NextRequest } from "next/server";
import {
  CopilotRuntime,
  ExperimentalEmptyAdapter,
  copilotRuntimeNextJSAppRouterEndpoint,
} from "@copilotkit/runtime";
import { LangGraphHttpAgent } from "@copilotkit/runtime/langgraph";

const AGUI_ENDPOINT =
  process.env.AGUI_ENDPOINT ?? "http://127.0.0.1:8001/agui";

const runtime = new CopilotRuntime({
  agents: {
    "ag-ui-langgraph": new LangGraphHttpAgent({
      url: AGUI_ENDPOINT,
      agentId: "ag-ui-langgraph",
      description: "AG-UI LangGraph agent",
    }) as unknown as any,
  },
});

const { handleRequest } = copilotRuntimeNextJSAppRouterEndpoint({
  runtime,
  serviceAdapter: new ExperimentalEmptyAdapter(),
  endpoint: "/api/copilotkit",
  cors: {
    origin: ["http://localhost:3000", "http://127.0.0.1:3000"],
    credentials: true,
  },
});

export async function POST(req: NextRequest) {
  return handleRequest(req);
}

export async function GET(req: NextRequest) {
  return handleRequest(req);
}
