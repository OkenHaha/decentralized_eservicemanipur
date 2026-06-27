import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class BlockchainLedgerEntry(Base):
    __tablename__ = "blockchain_ledger"

    block_hash = Column(String(64), primary_key=True)  # SHA-256 hash of this block data
    application_id = Column(String(50), ForeignKey("applications.application_id"), nullable=False, index=True)
    previous_block_hash = Column(String(64), nullable=True)  # Hash of previous block, forming the chain
    aggregate_data_hash = Column(String(64), nullable=False)  # SHA-256 fingerprint of current state
    status_at_block = Column(String(50), nullable=False)
    signee_address = Column(String(100), nullable=False)  # wallet address / public key of official
    signee_role = Column(String(50), nullable=False)  # ROLE of official or SYSTEM
    action_description = Column(Text, nullable=True)
    block_timestamp = Column(DateTime, default=datetime.utcnow)
    block_sequence = Column(Integer, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="ledger_entries")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(String(36), primary_key=True, default=generate_uuid)
    entity_type = Column(String(50), nullable=False)  # CITIZEN, APPLICATION, OFFICIAL, DOCUMENT, CERTIFICATE
    entity_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # CREATE, READ, UPDATE, DELETE, LOGIN, VERIFY
    actor_id = Column(String(50), nullable=False)  # citizen_id, official_id, or system
    actor_type = Column(String(20), nullable=False)  # CITIZEN, OFFICIAL, SYSTEM
    actor_ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(255), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    performed_at = Column(DateTime, default=datetime.utcnow)
