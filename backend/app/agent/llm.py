"""
Thin wrapper around Groq's chat completion API via langchain-groq.

Primary model: gemma2-9b-it (fast, cheap -> good for routine extraction/summarization)
Fallback model: llama-3.3-70b-versatile (used if the primary model errors out or
for tasks that need stronger reasoning, e.g. resolving ambiguous free-text notes)
"""
from langchain_groq import ChatGroq
from app.config import settings


def get_llm(model: str = None, temperature: float = 0.2):
    """Return a ChatGroq client. Falls back to the larger model on request."""
    model_name = model or settings.GROQ_MODEL
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model=model_name,
        temperature=temperature,
    )


def get_llm_with_fallback():
    """
    Returns the primary (gemma2-9b-it) LLM, and a fallback (llama-3.3-70b-versatile)
    that agent tools can call if the primary model fails or if the task is flagged
    as needing deeper reasoning (e.g. a long, messy free-text note).
    """
    primary = get_llm(settings.GROQ_MODEL, temperature=0.2)
    fallback = get_llm(settings.GROQ_MODEL_FALLBACK, temperature=0.2)
    return primary, fallback
