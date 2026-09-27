from sqlalchemy import text
from sqlalchemy.orm import Session
import os
import uuid
import logging

from database import engine, SessionLocal, Base
from models import User, ProspectAnalysisDB
from auth.security import get_password_hash

logger = logging.getLogger(__name__)

def init_db():
    """
    Initializes database tables, executes schema migrations for UUIDs,
    and seeds default system admin user.
    """
    # Step 1: Create all tables if they do not exist
    Base.metadata.create_all(bind=engine)

    # Step 2: Run safe schema migrations and seed admin user
    try:
        with engine.connect() as conn:
            # 1. Ensure uuid, OAuth columns exist on users table
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS uuid VARCHAR(36);"))
            conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_uuid ON users (uuid);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_provider VARCHAR(50) DEFAULT 'local';"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR(255);"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_users_google_id ON users (google_id);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500);"))
            try:
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL;"))
            except Exception:
                pass

            # 2. Ensure user_uuid and all data columns exist on analyses table
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS user_uuid VARCHAR(36);"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS user_id INTEGER;"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_analyses_user_uuid ON analyses (user_uuid);"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS avg_confidence_level VARCHAR;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS overall_quality_score FLOAT DEFAULT 75.0;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS critical_data_gaps JSON;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS data_freshness VARCHAR;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS data_grounding VARCHAR DEFAULT 'grounded';"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS parameters_fully_analyzed JSON;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS parameters_partial_data JSON;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS parameters_insufficient JSON;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS chat_history JSON DEFAULT '[]'::json;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS analysis_mode VARCHAR DEFAULT 'GENERAL';"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS proposal_details JSON;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS proposal_filename VARCHAR;"))
            conn.execute(text("ALTER TABLE analyses ADD COLUMN IF NOT EXISTS risk_rating VARCHAR;"))
            conn.commit()
            logger.info("Database schema columns verified; chat_history JSON column active.")

        # 3. Check and optionally seed default admin user
        seed_admin_flag = os.getenv("SEED_DEFAULT_ADMIN", "false").strip().lower() in ("true", "1", "yes")
        db: Session = SessionLocal()
        try:
            admin_email = os.getenv("DEFAULT_ADMIN_EMAIL", "admin@example.com").strip().lower()
            admin_user = db.query(User).filter(User.email == admin_email).first()

            if not admin_user and seed_admin_flag:
                admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "Admin@123")
                logger.info("SEED_DEFAULT_ADMIN is enabled. Seeding initial system admin user: %s", admin_email)
                admin_user = User(
                    uuid=str(uuid.uuid4()),
                    name="System Admin",
                    email=admin_email,
                    password_hash=get_password_hash(admin_password),
                    role="admin",
                    is_active=True
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
                logger.info("Initial admin user created with UUID: %s", admin_user.uuid)
            elif admin_user:
                if not admin_user.uuid:
                    admin_user.uuid = str(uuid.uuid4())
                    db.commit()
                    db.refresh(admin_user)
                logger.info("Admin user verified (UUID: %s).", admin_user.uuid)

            # 4. Associate unassigned existing analysis records with user UUIDs
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE analyses 
                    SET user_uuid = users.uuid 
                    FROM users 
                    WHERE analyses.user_id = users.id 
                      AND (analyses.user_uuid IS NULL OR analyses.user_uuid = '');
                """))
                if admin_user:
                    conn.execute(text("""
                        UPDATE analyses 
                        SET user_uuid = :admin_uuid 
                        WHERE user_uuid IS NULL OR user_uuid = '';
                    """), {"admin_uuid": admin_user.uuid})
                conn.commit()

            total_analyses = db.query(ProspectAnalysisDB).count()
            logger.info("Total analysis records verified: %d", total_analyses)

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Migration / Seeding note: {e}")
