from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_migrations():
    """Safely add new columns to existing tables (idempotent)."""
    with engine.connect() as conn:
        def _cols(table: str) -> set:
            result = conn.execute(text(f"PRAGMA table_info({table})"))
            return {row[1] for row in result}

        # tickets
        ticket_cols = _cols("tickets")
        if "monat" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN monat INTEGER"))
        if "jahr" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN jahr INTEGER"))
        if "eskalationsstufe" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN eskalationsstufe TEXT"))

        # ticket_kommentare
        kom_cols = _cols("ticket_kommentare")
        if "ist_intern" not in kom_cols:
            conn.execute(text(
                "ALTER TABLE ticket_kommentare ADD COLUMN ist_intern BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        if "zitat_id" not in kom_cols:
            conn.execute(text(
                "ALTER TABLE ticket_kommentare ADD COLUMN zitat_id INTEGER REFERENCES ticket_kommentare(id)"
            ))

        # mandanten – onboarding flag
        mandant_cols = _cols("mandanten")
        if "onboarding_abgeschlossen" not in mandant_cols:
            conn.execute(text(
                "ALTER TABLE mandanten ADD COLUMN onboarding_abgeschlossen BOOLEAN DEFAULT FALSE"
            ))

        # workflow_vorlagen – onboarding flag
        vl_cols = _cols("workflow_vorlagen")
        if "ist_onboarding" not in vl_cols:
            conn.execute(text(
                "ALTER TABLE workflow_vorlagen ADD COLUMN ist_onboarding BOOLEAN DEFAULT FALSE"
            ))

        # workflow_instanzen – re-open fields
        wi_cols = _cols("workflow_instanzen")
        if "wiedereroeffnet_am" not in wi_cols:
            conn.execute(text(
                "ALTER TABLE workflow_instanzen ADD COLUMN wiedereroeffnet_am DATETIME"
            ))
        if "wiedereroeffnet_begruendung" not in wi_cols:
            conn.execute(text(
                "ALTER TABLE workflow_instanzen ADD COLUMN wiedereroeffnet_begruendung TEXT"
            ))

        # dokumente – logical delete
        dok_cols = _cols("dokumente")
        if "ist_geloescht" not in dok_cols:
            conn.execute(text(
                "ALTER TABLE dokumente ADD COLUMN ist_geloescht BOOLEAN DEFAULT FALSE"
            ))

        conn.commit()
