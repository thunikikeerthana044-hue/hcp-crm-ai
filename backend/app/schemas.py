from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List, Any
import datetime


# ---------- HCP ----------
class HCPBase(BaseModel):
    name: str
    specialty: Optional[str] = None
    institution: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    territory: Optional[str] = None
    preferred_channel: Optional[str] = "In-Person"


class HCPCreate(HCPBase):
    pass


class HCPOut(HCPBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime.datetime


# ---------- Interaction ----------
class InteractionBase(BaseModel):
    hcp_id: str
    interaction_type: Optional[str] = "Visit"
    channel: Optional[str] = "In-Person"
    interaction_date: Optional[datetime.datetime] = None
    products_discussed: Optional[str] = None
    topics: Optional[str] = None
    sentiment: Optional[str] = None
    samples_dropped: Optional[str] = None
    materials_shared: Optional[str] = None
    key_takeaways: Optional[str] = None
    next_steps: Optional[str] = None
    follow_up_date: Optional[datetime.datetime] = None
    raw_notes: Optional[str] = None


class InteractionCreate(InteractionBase):
    pass


class InteractionUpdate(BaseModel):
    interaction_type: Optional[str] = None
    channel: Optional[str] = None
    products_discussed: Optional[str] = None
    topics: Optional[str] = None
    sentiment: Optional[str] = None
    samples_dropped: Optional[str] = None
    materials_shared: Optional[str] = None
    key_takeaways: Optional[str] = None
    next_steps: Optional[str] = None
    follow_up_date: Optional[datetime.datetime] = None
    raw_notes: Optional[str] = None
    edit_reason: Optional[str] = None


class InteractionOut(InteractionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    ai_summary: Optional[str] = None
    source: str
    compliance_flag: bool
    compliance_notes: Optional[str] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


# ---------- Chat ----------
class ChatMessageIn(BaseModel):
    session_id: Optional[str] = None
    message: str
    rep_id: Optional[str] = "demo-rep"


class ChatMessageOut(BaseModel):
    session_id: str
    reply: str
    tool_calls: List[Any] = Field(default_factory=list)
    pending_interaction: Optional[dict] = None
    interaction_saved: Optional[InteractionOut] = None
