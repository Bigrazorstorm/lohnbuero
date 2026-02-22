from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# MySQL requires pymysql driver and doesn't need check_same_thread
connect_args = {}
if not settings.database_url.startswith("sqlite"):
    connect_args = {"charset": "utf8mb4"}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
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

        # users – workload fields
        user_cols = _cols("users")
        if "workload_limit" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN workload_limit REAL DEFAULT 100.0"
            ))
        if "current_workload" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN current_workload REAL DEFAULT 0.0"
            ))
        if "total_points_earned" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN total_points_earned REAL DEFAULT 0.0"
            ))
        if "is_archived" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN is_archived BOOLEAN DEFAULT FALSE"
            ))
        if "anonymisiert_am" not in user_cols:
            conn.execute(text(
                "ALTER TABLE users ADD COLUMN anonymisiert_am DATETIME"
            ))

        # tickets – new fields (v1.5)
        ticket_cols = _cols("tickets")
        if "unterkategorie" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN unterkategorie TEXT"))
        if "wiedervorlage_datum" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN wiedervorlage_datum DATETIME"))
        if "abbruch_grund" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN abbruch_grund TEXT"))
        if "workflow_item_id" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN workflow_item_id INTEGER"))

        # workflow_items – new fields (v1.5)
        item_cols = _cols("workflow_items")
        if "zugewiesen_an_id" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN zugewiesen_an_id INTEGER"))
        if "fristart_referenz" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN fristart_referenz TEXT"))
        if "ist_blockiert" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN ist_blockiert BOOLEAN DEFAULT FALSE"))
        if "blockiert_grund" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN blockiert_grund TEXT"))

        # workflow_vorlage_items – new fields (v1.5)
        vli_cols = _cols("workflow_vorlage_items")
        if "ist_optional_pro_mandant" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN ist_optional_pro_mandant BOOLEAN DEFAULT FALSE"))
        if "fristart_referenz" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN fristart_referenz TEXT"))
        if "fristart_offset_tage" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN fristart_offset_tage INTEGER DEFAULT 0"))
        if "standard_punkte" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN standard_punkte REAL DEFAULT 1.0"))

        conn.commit()
