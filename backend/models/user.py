import uuid
import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship, foreign
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)
    auth_provider = Column(String(50), default="local", nullable=False)
    google_id = Column(String(255), unique=True, index=True, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    role = Column(String(50), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc), nullable=False)

    # 1-to-many relationship: One User has Many Prospect Analyses linked by UUID
    analyses = relationship(
        "ProspectAnalysisDB",
        primaryjoin="User.uuid == foreign(ProspectAnalysisDB.user_uuid)",
        back_populates="user",
        cascade="all, delete-orphan"
    )
