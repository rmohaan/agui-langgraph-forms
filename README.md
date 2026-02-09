# AG-UI Forms (Gemini + CopilotKit demo)

## Structure
- `backend/app`: FastAPI backend (Pydantic AI + LangGraph scaffolding)
- `frontend`: Next.js frontend 

## Backend
```bash
cd backend/app
python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env

cd /agui-langgraph-forms/  
touch backend/app/__init__.py                                       
touch backend/app/graph/__init__.py   
cd backend
python3.12 -m uvicorn main:app --reload --port 8001   
```

## Frontend
```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Notes
- `LLM_PROVIDER` supports `gemini`, `ollama`, or `mock`.
- Streaming updates come from `/stream/{jobId}` as AG-UI events.
