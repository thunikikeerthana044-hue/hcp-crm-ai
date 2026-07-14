import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, messages_from_dict, messages_to_dict

from app.database import get_db
from app import models, schemas
from app.agent.graph import compiled_agent_graph

router = APIRouter(prefix="/api/chat", tags=["Chat Agent"])


@router.post("/message", response_model=schemas.ChatMessageOut)
def send_message(payload: schemas.ChatMessageIn, hcp_id: str = None, db: Session = Depends(get_db)):
    """
    Conversational logging endpoint. Pass an existing session_id to continue
    a conversation, or omit it to start a new one. Pass hcp_id (query param)
    on the first message to tell the agent which HCP this conversation is about.
    """
    if payload.session_id:
        session = db.query(models.ChatSession).filter(models.ChatSession.id == payload.session_id).first()
        if not session:
            raise HTTPException(404, "Chat session not found")
        prior_messages = messages_from_dict(json.loads(session.messages or "[]"))
    else:
        session = models.ChatSession(id=str(uuid.uuid4()), rep_id=payload.rep_id, messages="[]")
        db.add(session)
        db.commit()
        prior_messages = []

    prior_messages.append(HumanMessage(content=payload.message))

    result = compiled_agent_graph.invoke({
        "messages": prior_messages,
        "hcp_id": hcp_id or "",
    })

    final_messages = result["messages"]
    session.messages = json.dumps(messages_to_dict(final_messages))
    db.commit()

    # Collect tool call info + the final AI reply text
    tool_calls_summary = []
    saved_interaction = None
    for m in final_messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls_summary.append({"tool": tc["name"], "args": tc["args"]})
        if isinstance(m, ToolMessage) and m.name == "log_interaction":
            try:
                parsed = json.loads(m.content)
                if "id" in parsed:
                    saved = db.query(models.Interaction).filter(models.Interaction.id == parsed["id"]).first()
                    if saved:
                        saved_interaction = saved
            except Exception:
                pass

    last_ai_message = next((m for m in reversed(final_messages) if isinstance(m, AIMessage)), None)
    reply_text = last_ai_message.content if last_ai_message else ""

    return schemas.ChatMessageOut(
        session_id=session.id,
        reply=reply_text,
        tool_calls=tool_calls_summary,
        interaction_saved=saved_interaction,
    )
