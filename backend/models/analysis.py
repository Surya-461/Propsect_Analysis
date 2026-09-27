import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class ProspectAnalysisDB(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_uuid = Column(String(36), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    company_name = Column(String, index=True)
    report_data = Column(JSON)
    executive_summary = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)
    avg_confidence_level = Column(String, nullable=True)
    overall_quality_score = Column(Float, default=75.0)
    critical_data_gaps = Column(JSON, nullable=True)
    data_freshness = Column(String, nullable=True)
    data_grounding = Column(String, default="grounded")
    parameters_fully_analyzed = Column(JSON, nullable=True)
    parameters_partial_data = Column(JSON, nullable=True)
    parameters_insufficient = Column(JSON, nullable=True)
    analysis_mode = Column(String, default="GENERAL", nullable=False)
    proposal_details = Column(JSON, nullable=True)
    proposal_filename = Column(String, nullable=True)
    risk_rating = Column(String, nullable=True)
    chat_history = Column(JSON, default=list, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    pipeline_version = Column(String, default="2.1.0", nullable=True)

    # Relationship back to User via UUID
    user = relationship(
        "User",
        primaryjoin="foreign(ProspectAnalysisDB.user_uuid) == User.uuid",
        back_populates="analyses"
    )

# Backward compatibility alias
ProspectAnalysis = ProspectAnalysisDB
