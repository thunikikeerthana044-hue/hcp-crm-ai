import datetime
import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Boolean, Integer, Float
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id():
    return str(uuid.uuid4())


class HCP(Base):
    """A Healthcare Professional the field rep engages with."""
    __tablename__ = "hcps"

    id = Column(String(36), primary_key=True, default=gen_id)
    name = Column(String(255), nullable=False)
    specialty = Column(String(255))
    institution = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    territory = Column(String(255))
    preferred_channel = Column(String(50), default="In-Person")  # In-Person, Virtual, Phone, Email
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    interactions = relationship("Interaction", back_populates="hcp", cascade="all, delete-orphan")


class Interaction(Base):
    """A single logged interaction between a rep and an HCP."""
    __tablename__ = "interactions"

    id = Column(String(36), primary_key=True, default=gen_id)
    hcp_id = Column(String(36), ForeignKey("hcps.id"), nullable=False)

    interaction_type = Column(String(50))       # Visit, Call, Email, Virtual Meeting, Conference
    channel = Column(String(50))
    interaction_date = Column(DateTime, default=datetime.datetime.utcnow)

    products_discussed = Column(Text)            # comma-separated or JSON string
    topics = Column(Text)
    sentiment = Column(String(20))                # Positive, Neutral, Negative
    samples_dropped = Column(Text)                # JSON string: [{product, qty}]
    materials_shared = Column(Text)

    key_takeaways = Column(Text)
    next_steps = Column(Text)
    follow_up_date = Column(DateTime, nullable=True)

    raw_notes = Column(Text)                      # original free-text / transcript from rep
    ai_summary = Column(Text)                      # LLM-generated summary
    source = Column(String(20), default="form")   # "form" or "chat"

    compliance_flag = Column(Boolean, default=False)
    compliance_notes = Column(Text)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    edit_history = Column(Text)  # JSON string list of prior versions (audit trail)

    hcp = relationship("HCP", back_populates="interactions")


class ChatSession(Base):
    """Stores conversational agent state per rep session (for the chat logging mode)."""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=gen_id)
    rep_id = Column(String(100), default="demo-rep")
    messages = Column(Text)  # JSON string of the running message list
    pending_interaction = Column(Text)  # JSON string of the draft interaction being built
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
