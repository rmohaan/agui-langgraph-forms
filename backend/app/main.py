from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
# Note the specific integration path for the endpoint
from copilotkit.integrations.fastapi import add_fastapi_endpoint
from copilotkit import Action, CopilotKitRemoteEndpoint, LangGraphAGUIAgent
from ag_ui_langgraph import add_langgraph_fastapi_endpoint
from .graph.workflow import graph
# from ag_ui_langgraph import add_langgraph_fastapi_endpoint

app = FastAPI()

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# sdk = LangGraphAgent(
#     name="ag-ui-agent",
#     graph=graph, # Your compiled LangGraph
#     description="Agent for AG-UI application",
# )

def greet_user_handler(name):
    """Displays a simple, personalized greeting."""
    print(f"Hello, {name.title()}!")

if not hasattr(LangGraphAGUIAgent, "dict_repr"):
    LangGraphAGUIAgent.dict_repr = lambda self: {
        "name": self.name,
        "description": self.description,
    }

sdk = LangGraphAGUIAgent(
    name="ag-ui-langgraph",
    graph=graph, # Your compiled LangGraph
    description="Agent for AG-UI application",
)

actions=[
        Action(
            name="greet_user",
            handler=greet_user_handler,
            description="Greet the user",
            parameters=[
                {
                    "name": "name",
                    "type": "string",
                    "description": "The name of the user"
                }
            ]
        )
    ]

remote_endpoint = CopilotKitRemoteEndpoint(
    actions=actions,
    agents=[sdk]
)

# For local development, expose agents list on the runtime /info endpoint.
# The constructor doesn't accept `agents__unsafe_dev_only`; set it after init.
remote_endpoint.agents__unsafe_dev_only = [sdk]

add_fastapi_endpoint(app, remote_endpoint, "/copilotkit")
add_langgraph_fastapi_endpoint(app, sdk, "/agui")

# Simple test endpoint to verify the graph/agents and Ollama connectivity.
# POST JSON {"input_text": "..."} -> runs summarizer then counter and returns results.
@app.post("/test-graph")
async def test_graph(body: dict):
    input_text = body.get("input_text") if isinstance(body, dict) else None
    if not input_text:
        return {"error": "input_text is required"}

    try:
        from .agents.summarizer import summarizer_agent
        from .agents.counter import counter_agent

        # run summarizer against local Ollama (configured in agents)
        summ_res = await summarizer_agent.run(input_text)
        print("Summarizer response:", summ_res)

        # get summary text (handle different response shapes)
        summary_text = None
        if hasattr(summ_res, "data"):
            summary_text = getattr(summ_res.data, "summary", None) or getattr(summ_res.data, "text", None)
        else:
            summary_text = getattr(summ_res, "summary", None)

        # run counter using the summary
        count_res = await counter_agent.run(summary_text or input_text)
        print("Counter response:", count_res)

        return {
            "input_text": input_text,
            "summary": summ_res.data if hasattr(summ_res, "data") else summ_res,
            "count": count_res.data if hasattr(count_res, "data") else count_res,
        }
    except Exception as exc: # pylint: disable=broad-except
        return {"error": str(exc)}
