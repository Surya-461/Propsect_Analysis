from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.analysis import ProspectAnalysisDB
from models.user import User

class AnalysisRepository:
    @staticmethod
    def get_by_id(db: Session, analysis_id: int) -> Optional[ProspectAnalysisDB]:
        return db.query(ProspectAnalysisDB).filter(ProspectAnalysisDB.id == analysis_id).first()

    @staticmethod
    def get_by_id_and_user(db: Session, analysis_id: int, user: User) -> Optional[ProspectAnalysisDB]:
        query = db.query(ProspectAnalysisDB).filter(ProspectAnalysisDB.id == analysis_id)
        if user.role != "admin":
            query = query.filter(
                (ProspectAnalysisDB.user_uuid == user.uuid) | (ProspectAnalysisDB.user_id == user.id)
            )
        return query.first()

    @staticmethod
    def get_by_company(db: Session, company_name: str, user: Optional[User] = None) -> Optional[ProspectAnalysisDB]:
        query = db.query(ProspectAnalysisDB)
        if user and user.role != "admin":
            query = query.filter(
                (ProspectAnalysisDB.user_uuid == user.uuid) | (ProspectAnalysisDB.user_id == user.id)
            )
        return query.filter(
            ProspectAnalysisDB.company_name.ilike(f"%{company_name}%")
        ).order_by(ProspectAnalysisDB.created_at.desc()).first()

    @staticmethod
    def get_user_history(db: Session, user: User, limit: int = 50) -> List[ProspectAnalysisDB]:
        query = db.query(ProspectAnalysisDB)
        if user.role != "admin":
            query = query.filter(
                (ProspectAnalysisDB.user_uuid == user.uuid) | (ProspectAnalysisDB.user_id == user.id)
            )
        return query.order_by(ProspectAnalysisDB.created_at.desc()).limit(limit).all()

    @staticmethod
    def create(db: Session, **kwargs) -> ProspectAnalysisDB:
        analysis = ProspectAnalysisDB(**kwargs)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis

    @staticmethod
    def delete(db: Session, analysis: ProspectAnalysisDB) -> None:
        db.delete(analysis)
        db.commit()

    @staticmethod
    def save_chat_history(db: Session, analysis: ProspectAnalysisDB, new_history: List[Dict[str, Any]]) -> ProspectAnalysisDB:
        try:
            analysis.chat_history = list(new_history)
            db.add(analysis)
            db.commit()
            db.refresh(analysis)
            return analysis
        except Exception as e:
            db.rollback()
            raise RuntimeError(f"Failed to persist chat history for analysis_id={analysis.id}: {e}") from e
