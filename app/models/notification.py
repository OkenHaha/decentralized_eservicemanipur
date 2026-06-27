import uuid
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Text
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(String(36), primary_key=True, default=generate_uuid)
    recipient_id = Column(String(36), nullable=False)  # citizen_id or official_id
    recipient_type = Column(String(20), nullable=False)  # CITIZEN, OFFICIAL
    application_id = Column(String(50), nullable=True)
    channel = Column(String(20), default="SMS")  # SMS, EMAIL, IN_APP
    title = Column(String(100), nullable=False)
    message_body = Column(Text, nullable=False)
    notification_type = Column(String(50), nullable=False)  # STATUS_UPDATE, DOCUMENT_REQUEST, etc.
    is_read = Column(Boolean, default=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime, nullable=True)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
