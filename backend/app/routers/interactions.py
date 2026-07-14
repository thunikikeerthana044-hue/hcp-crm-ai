import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app import models, schemas
from app.agent.tools import check_compliance

router = APIRouter(prefix="/api/interactions", tags=["Interactions"])


@router.get("/", response_model=List[schemas.InteractionOut])
def list_interactions(hcp_id: str = None, db: Session = Depends(get_db)):
    q = db.query(models.Interaction)
    if hcp_id:
        q = q.filter(models.Interaction.hcp_id == hcp_id)
    return q.order_by(models.Interaction.interaction_date.desc()).all()


@router.post("/", response_model=schemas.InteractionOut)
def create_interaction(payload: schemas.InteractionCreate, db: Session = Depends(get_db)):
    """
    Structured-form submission path. The rep filled out the form directly
    (no chat), so we save the fields as given. We still run the LLM-backed
    compliance check tool, and (if raw_notes was provided instead of full
    fields) we could reuse log_interaction — kept separate here so the form
    path is fast and doesn't require an LLM round trip unless raw_notes is
    the primary content.
    """
    hcp = db.query(models.HCP).filter(models.HCP.id == payload.hcp_id).first()
    if not hcp:
        raise HTTPException(404, "HCP not found")

    interaction = models.Interaction(
        **payload.model_dump(exclude_unset=True, exclude={"interaction_date"}),
        source="form",
        edit_history="[]",
    )
    if payload.interaction_date:
        interaction.interaction_date = payload.interaction_date

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    # Run compliance check via the same tool the chat agent uses
    try:
        check_compliance.invoke({"interaction_id": interaction.id})
        db.refresh(interaction)
    except Exception:
        pass

    return interaction


@router.put("/{interaction_id}", response_model=schemas.InteractionOut)
def update_interaction(interaction_id: str, payload: schemas.InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")

    snapshot = {
        "interaction_type": interaction.interaction_type,
        "products_discussed": interaction.products_discussed,
        "topics": interaction.topics,
        "sentiment": interaction.sentiment,
        "samples_dropped": interaction.samples_dropped,
        "key_takeaways": interaction.key_takeaways,
        "next_steps": interaction.next_steps,
    }
    history = json.loads(interaction.edit_history or "[]")
    history.append({"previous_values": snapshot, "change_request": payload.edit_reason or "manual form edit"})
    interaction.edit_history = json.dumps(history)

    for field, value in payload.model_dump(exclude_unset=True, exclude={"edit_reason"}).items():
        setattr(interaction, field, value)

    db.commit()
    db.refresh(interaction)
    return interaction


@router.delete("/{interaction_id}")
def delete_interaction(interaction_id: str, db: Session = Depends(get_db)):
    interaction = db.query(models.Interaction).filter(models.Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(404, "Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"ok": True}
