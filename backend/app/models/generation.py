from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, String, Text

from app.models.conversation import Base, gen_id


class GenerationTask(Base):
    __tablename__ = "generation_tasks"

    id = Column(String, primary_key=True, default=gen_id)
    message_id = Column(String, ForeignKey("messages.id"), nullable=True)
    operation_id = Column(String, nullable=True)  # Google API operation ID
    status = Column(String, default="pending")  # pending | processing | completed | failed
    progress = Column(Float, default=0.0)
    result_url = Column(String, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
