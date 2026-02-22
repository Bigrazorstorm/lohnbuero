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
    from sqlalchemy import inspect
    
    with engine.connect() as conn:
        inspector = inspect(engine)
        
        # tickets
        ticket_cols = {col['name'] for col in inspector.get_columns('tickets')}
        if "monat" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN monat INTEGER"))
        if "jahr" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN jahr INTEGER"))
        if "eskalationsstufe" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN eskalationsstufe TEXT"))

        # ticket_kommentare
        kom_cols = {col['name'] for col in inspector.get_columns('ticket_kommentare')}
        if "ist_intern" not in kom_cols:
            conn.execute(text(
                "ALTER TABLE ticket_kommentare ADD COLUMN ist_intern BOOLEAN NOT NULL DEFAULT FALSE"
            ))
        if "zitat_id" not in kom_cols:
            conn.execute(text(
                "ALTER TABLE ticket_kommentare ADD COLUMN zitat_id INTEGER REFERENCES ticket_kommentare(id)"
            ))

        # mandanten – onboarding flag
        mandant_cols = {col['name'] for col in inspector.get_columns('mandanten')}
        if "onboarding_abgeschlossen" not in mandant_cols:
            conn.execute(text(
                "ALTER TABLE mandanten ADD COLUMN onboarding_abgeschlossen BOOLEAN DEFAULT FALSE"
            ))

        # workflow_vorlagen – onboarding flag
        vl_cols = {col['name'] for col in inspector.get_columns('workflow_vorlagen')}
        if "ist_onboarding" not in vl_cols:
            conn.execute(text(
                "ALTER TABLE workflow_vorlagen ADD COLUMN ist_onboarding BOOLEAN DEFAULT FALSE"
            ))

        # workflow_instanzen – re-open fields
        wi_cols = {col['name'] for col in inspector.get_columns('workflow_instanzen')}
        if "wiedereroeffnet_am" not in wi_cols:
            conn.execute(text(
                "ALTER TABLE workflow_instanzen ADD COLUMN wiedereroeffnet_am DATETIME"
            ))
        if "wiedereroeffnet_begruendung" not in wi_cols:
            conn.execute(text(
                "ALTER TABLE workflow_instanzen ADD COLUMN wiedereroeffnet_begruendung TEXT"
            ))

        # dokumente – logical delete
        dok_cols = {col['name'] for col in inspector.get_columns('dokumente')}
        if "ist_geloescht" not in dok_cols:
            conn.execute(text(
                "ALTER TABLE dokumente ADD COLUMN ist_geloescht BOOLEAN DEFAULT FALSE"
            ))

        # users – workload fields
        user_cols = {col['name'] for col in inspector.get_columns('users')}
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
        if "unterkategorie" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN unterkategorie TEXT"))
        if "wiedervorlage_datum" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN wiedervorlage_datum DATETIME"))
        if "abbruch_grund" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN abbruch_grund TEXT"))
        if "workflow_item_id" not in ticket_cols:
            conn.execute(text("ALTER TABLE tickets ADD COLUMN workflow_item_id INTEGER"))

        # workflow_items – new fields (v1.5)
        item_cols = {col['name'] for col in inspector.get_columns('workflow_items')}
        if "zugewiesen_an_id" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN zugewiesen_an_id INTEGER"))
        if "fristart_referenz" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN fristart_referenz TEXT"))
        if "ist_blockiert" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN ist_blockiert BOOLEAN DEFAULT FALSE"))
        if "blockiert_grund" not in item_cols:
            conn.execute(text("ALTER TABLE workflow_items ADD COLUMN blockiert_grund TEXT"))

        # workflow_vorlage_items – new fields (v1.5)
        vli_cols = {col['name'] for col in inspector.get_columns('workflow_vorlage_items')}
        if "ist_optional_pro_mandant" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN ist_optional_pro_mandant BOOLEAN DEFAULT FALSE"))
        if "fristart_referenz" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN fristart_referenz TEXT"))
        if "fristart_offset_tage" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN fristart_offset_tage INTEGER DEFAULT 0"))
        if "standard_punkte" not in vli_cols:
            conn.execute(text("ALTER TABLE workflow_vorlage_items ADD COLUMN standard_punkte REAL DEFAULT 1.0"))

        # workflow_instanzen – erledigt_von and faellig fields for kernel processes
        wi_cols = {col['name'] for col in inspector.get_columns('workflow_instanzen')}
        if "unterlagen_eingegangen_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN unterlagen_eingegangen_von_id INTEGER"))
        if "unterlagen_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN unterlagen_faellig DATETIME"))
        if "probe_abrechnung_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN probe_abrechnung_von_id INTEGER"))
        if "probe_abrechnung_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN probe_abrechnung_faellig DATETIME"))
        if "probe_geprueft_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN probe_geprueft_von_id INTEGER"))
        if "probe_geprueft_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN probe_geprueft_faellig DATETIME"))
        if "mandant_freigabe_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN mandant_freigabe_von_id INTEGER"))
        if "mandant_freigabe_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN mandant_freigabe_faellig DATETIME"))
        if "endabrechnung_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN endabrechnung_von_id INTEGER"))
        if "endabrechnung_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN endabrechnung_faellig DATETIME"))
        if "versand_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN versand_von_id INTEGER"))
        if "versand_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN versand_faellig DATETIME"))
        if "abgeschlossen_von_id" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN abgeschlossen_von_id INTEGER"))
        if "abgeschlossen_faellig" not in wi_cols:
            conn.execute(text("ALTER TABLE workflow_instanzen ADD COLUMN abgeschlossen_faellig DATETIME"))

        # audit_logs – add foreign key for benutzer_id
        audit_cols = {col['name'] for col in inspector.get_columns('audit_logs')}
        # Note: Foreign key constraint may already exist, but we ensure the column is there
        if "benutzer_id" not in audit_cols:
            conn.execute(text("ALTER TABLE audit_logs ADD COLUMN benutzer_id INTEGER"))

        conn.commit()
