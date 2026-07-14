"""
The LangGraph agent's toolbox.

Each tool is a discrete, auditable action the agent can take on behalf of the
field rep. Tools that touch the database open their own short-lived session
(the agent runs outside the normal FastAPI request/response cycle).

Tools implemented (6 total, 5 minimum required by the brief):
  1. log_interaction        - REQUIRED. Parses free text -> structured interaction, saves it.
  2. edit_interaction       - REQUIRED. Modifies a previously logged interaction, keeps an audit trail.
  3. get_hcp_history        - Pulls prior interactions so the agent has context before logging.
  4. schedule_follow_up     - Sets/updates a follow-up date + reminder note on an interaction.
  5. check_compliance       - Flags content that looks off-label / over sample-limits for MLR review.
  6. suggest_next_best_action - Recommends talking points/products for the *next* visit, based on history.
"""
import json
import datetime
from typing import Optional, List
from langchain_core.tools import tool

from app.database import SessionLocal
from app import models
from app.agent.llm import get_llm

EXTRACTION_SYSTEM_PROMPT = """You are a life-sciences CRM assistant. Extract structured fields from a \
field rep's raw note about a visit to a Healthcare Professional (HCP). \
Return ONLY valid JSON (no markdown, no commentary) with these exact keys:
{
  "interaction_type": one of ["Visit","Call","Email","Virtual Meeting","Conference"],
  "products_discussed": comma-separated string of product names mentioned, or "",
  "topics": short comma-separated string of clinical/discussion topics, or "",
  "sentiment": one of ["Positive","Neutral","Negative"],
  "samples_dropped": JSON-array-as-string of {"product":..., "qty":...} objects, or "[]",
  "key_takeaways": 1-2 sentence summary of what the HCP said or decided,
  "next_steps": 1 sentence on the agreed next action, or "",
  "summary": a concise 2-3 sentence professional summary of the whole interaction
}
"""

COMPLIANCE_SYSTEM_PROMPT = """You are a pharma compliance reviewer. Given an interaction summary, \
flag ONLY if there is a plausible off-label promotion claim, an unsubstantiated efficacy/safety claim, \
or an excessive sample quantity (>10 units of one product). Return ONLY valid JSON:
{"flag": true/false, "notes": "short explanation, empty string if flag is false"}
"""


def _llm_json(system_prompt: str, user_content: str) -> dict:
    """Call the Groq LLM and parse a JSON object out of its reply, defensively."""
    llm = get_llm()
    try:
        resp = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ])
        text = resp.content.strip()
        # Strip accidental markdown fences
        if text.startswith("```"):
            text = text.strip("`")
            text = text.split("\n", 1)[1] if "\n" in text else text
            text = text.replace("json\n", "", 1)
        return json.loads(text)
    except Exception:
        # Fall back to the larger model once before giving up
        try:
            from app.config import settings
            llm2 = get_llm(settings.GROQ_MODEL_FALLBACK)
            resp = llm2.invoke([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ])
            text = resp.content.strip().strip("`")
            return json.loads(text)
        except Exception as e:
            return {"_error": str(e)}


# ---------------------------------------------------------------------------
# TOOL 1 (REQUIRED): log_interaction
# ---------------------------------------------------------------------------
@tool
def log_interaction(hcp_id: str, raw_notes: str, source: str = "chat") -> str:
    """Log a new HCP interaction from a field rep's free-text note.
    Uses the LLM to extract interaction_type, products discussed, topics,
    sentiment, samples dropped, key takeaways, next steps, and a summary,
    then persists a structured Interaction row. Returns a JSON string of the
    saved interaction, including its id, so the caller (or a later
    edit_interaction call) can reference it."""
    extracted = _llm_json(EXTRACTION_SYSTEM_PROMPT, raw_notes)
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})

        samples_dropped = extracted.get("samples_dropped", "[]")
        if isinstance(samples_dropped, (dict, list)):
            samples_dropped = json.dumps(samples_dropped)
            
        topics = extracted.get("topics", "")
        if isinstance(topics, list):
            topics = ", ".join(topics)

        products_discussed = extracted.get("products_discussed", "")
        if isinstance(products_discussed, list):
            products_discussed = ", ".join(products_discussed)

        interaction = models.Interaction(
            hcp_id=hcp_id,
            interaction_type=extracted.get("interaction_type", "Visit"),
            channel=hcp.preferred_channel,
            interaction_date=datetime.datetime.utcnow(),
            products_discussed=products_discussed,
            topics=topics,
            sentiment=extracted.get("sentiment", "Neutral"),
            samples_dropped=samples_dropped,
            key_takeaways=extracted.get("key_takeaways", ""),
            next_steps=extracted.get("next_steps", ""),
            raw_notes=raw_notes,
            ai_summary=extracted.get("summary", ""),
            source=source,
            edit_history="[]",
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)
        return json.dumps({
            "id": interaction.id,
            "hcp_name": hcp.name,
            "interaction_type": interaction.interaction_type,
            "products_discussed": interaction.products_discussed,
            "sentiment": interaction.sentiment,
            "summary": interaction.ai_summary,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 2 (REQUIRED): edit_interaction
# ---------------------------------------------------------------------------
@tool
def edit_interaction(interaction_id: str, changes_description: str) -> str:
    """Edit a previously logged interaction. `changes_description` is a natural
    language description of what should change (e.g. "change sentiment to
    Positive and add that 5 samples of Drug A were dropped"). The LLM converts
    this into field updates, applies them, and stores the prior version in an
    audit trail (edit_history) before overwriting. Returns the updated
    interaction as a JSON string."""
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        current_snapshot = {
            "interaction_type": interaction.interaction_type,
            "products_discussed": interaction.products_discussed,
            "topics": interaction.topics,
            "sentiment": interaction.sentiment,
            "samples_dropped": interaction.samples_dropped,
            "key_takeaways": interaction.key_takeaways,
            "next_steps": interaction.next_steps,
        }

        edit_prompt = f"""Here is the CURRENT interaction record (JSON):
{json.dumps(current_snapshot)}

The rep wants this change: "{changes_description}"

Return ONLY a JSON object with the SAME keys as the current record, containing
the FULL updated values (unchanged fields copied as-is, changed fields updated)."""

        updated = _llm_json(
            "You update structured CRM interaction records based on a rep's natural-language edit request. "
            "Always return the complete record JSON, not a diff.",
            edit_prompt,
        )
        if "_error" in updated:
            return json.dumps({"error": "Could not parse edit", "detail": updated["_error"]})

        # audit trail: keep the pre-edit snapshot
        history = json.loads(interaction.edit_history or "[]")
        history.append({
            "edited_at": datetime.datetime.utcnow().isoformat(),
            "previous_values": current_snapshot,
            "change_request": changes_description,
        })
        interaction.edit_history = json.dumps(history)

        for key in current_snapshot.keys():
            if key in updated:
                val = updated[key]
                if isinstance(val, (dict, list)):
                    val = json.dumps(val)
                setattr(interaction, key, val)

        db.commit()
        db.refresh(interaction)
        return json.dumps({
            "id": interaction.id,
            "interaction_type": interaction.interaction_type,
            "products_discussed": interaction.products_discussed,
            "sentiment": interaction.sentiment,
            "key_takeaways": interaction.key_takeaways,
            "edit_count": len(history),
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 3: get_hcp_history
# ---------------------------------------------------------------------------
@tool
def get_hcp_history(hcp_id: str, limit: int = 5) -> str:
    """Retrieve the N most recent past interactions for an HCP, so the agent
    has context (previously discussed products, sentiment trend, open next
    steps) before logging a new interaction or making a recommendation."""
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})
        rows = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(limit)
            .all()
        )
        history = [{
            "id": r.id,
            "date": r.interaction_date.isoformat() if r.interaction_date else None,
            "type": r.interaction_type,
            "products_discussed": r.products_discussed,
            "sentiment": r.sentiment,
            "next_steps": r.next_steps,
            "summary": r.ai_summary,
        } for r in rows]
        return json.dumps({"hcp_name": hcp.name, "specialty": hcp.specialty, "history": history})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 4: schedule_follow_up
# ---------------------------------------------------------------------------
@tool
def schedule_follow_up(interaction_id: str, follow_up_date: str, note: Optional[str] = "") -> str:
    """Schedule (or update) a follow-up date on a logged interaction, e.g.
    '2026-08-01'. Optionally attach a short note describing what the follow-up
    should cover. This is what powers the rep's next-visit task list."""
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})
        try:
            parsed_date = datetime.datetime.fromisoformat(follow_up_date)
        except ValueError:
            return json.dumps({"error": f"Could not parse date '{follow_up_date}', use YYYY-MM-DD"})

        interaction.follow_up_date = parsed_date
        if note:
            interaction.next_steps = (interaction.next_steps or "") + f" | Follow-up: {note}"
        db.commit()
        return json.dumps({
            "id": interaction.id,
            "follow_up_date": interaction.follow_up_date.isoformat(),
            "next_steps": interaction.next_steps,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 5: check_compliance
# ---------------------------------------------------------------------------
@tool
def check_compliance(interaction_id: str) -> str:
    """Run an automated compliance check on a logged interaction (off-label
    claims, unsubstantiated efficacy/safety claims, excessive sample
    quantities). Flags the record for MLR/compliance review if needed and
    stores the reviewer notes."""
    db = SessionLocal()
    try:
        interaction = db.query(models.Interaction).filter(
            models.Interaction.id == interaction_id
        ).first()
        if not interaction:
            return json.dumps({"error": f"No interaction found with id {interaction_id}"})

        content = (
            f"Products discussed: {interaction.products_discussed}\n"
            f"Topics: {interaction.topics}\n"
            f"Samples dropped: {interaction.samples_dropped}\n"
            f"Key takeaways: {interaction.key_takeaways}\n"
            f"Raw notes: {interaction.raw_notes}"
        )
        result = _llm_json(COMPLIANCE_SYSTEM_PROMPT, content)
        flag = bool(result.get("flag", False))
        notes = result.get("notes", "")

        interaction.compliance_flag = flag
        interaction.compliance_notes = notes
        db.commit()
        return json.dumps({"id": interaction.id, "compliance_flag": flag, "compliance_notes": notes})
    finally:
        db.close()


# ---------------------------------------------------------------------------
# TOOL 6 (bonus): suggest_next_best_action
# ---------------------------------------------------------------------------
@tool
def suggest_next_best_action(hcp_id: str) -> str:
    """Suggest talking points and product focus for the rep's NEXT interaction
    with this HCP, based on their interaction history (recent sentiment,
    products already discussed, open next steps)."""
    db = SessionLocal()
    try:
        hcp = db.query(models.HCP).filter(models.HCP.id == hcp_id).first()
        if not hcp:
            return json.dumps({"error": f"No HCP found with id {hcp_id}"})
        rows = (
            db.query(models.Interaction)
            .filter(models.Interaction.hcp_id == hcp_id)
            .order_by(models.Interaction.interaction_date.desc())
            .limit(5)
            .all()
        )
        history_text = "\n".join(
            f"- {r.interaction_date}: {r.ai_summary or r.key_takeaways} (sentiment: {r.sentiment})"
            for r in rows
        ) or "No prior interactions."

        prompt = f"HCP: {hcp.name}, specialty: {hcp.specialty}\nHistory:\n{history_text}\n\n" \
                 "Suggest 2-3 concrete talking points and a product focus for the next visit."
        llm = get_llm()
        resp = llm.invoke([
            {"role": "system", "content": "You are a helpful, compliant pharma sales strategy assistant."},
            {"role": "user", "content": prompt},
        ])
        return json.dumps({"hcp_name": hcp.name, "recommendation": resp.content.strip()})
    finally:
        db.close()


ALL_TOOLS = [
    log_interaction,
    edit_interaction,
    get_hcp_history,
    schedule_follow_up,
    check_compliance,
    suggest_next_best_action,
]
