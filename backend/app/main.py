import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph")
warnings.filterwarnings("ignore", message=".*allowed_objects.*", category=Warning)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import hcp, interactions, chat
from app import models  # noqa: F401  (ensures models are registered before create_all)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-First HCP CRM API",
    description="Backend for the Log Interaction screen: structured form + LangGraph conversational agent.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(hcp.router)
app.include_router(interactions.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "hcp-crm-ai backend"}


@app.get("/api/health")
def health():
    return {"status": "healthy", "groq_key_configured": bool(settings.GROQ_API_KEY)}
