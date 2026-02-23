from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import Base, engine, run_migrations, SessionLocal
from app.routers import admin, auth, dashboard, dokumente, mandanten, tickets, users, workflows
from app.routers import audit, email_templates
from app.routers import fristen, schritt_typen, reporting, global_events
from app.models import User

# Create all tables (new ones)
try:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created")
except Exception as e:
    print(f"✗ Error creating tables: {e}")
    raise

# Safely migrate existing tables (add new columns)
try:
    print("Running migrations...")
    run_migrations()
    print("✓ Migrations complete")
except Exception as e:
    print(f"✗ Error during migrations: {e}")
    import traceback
    traceback.print_exc()

# Auto-seed the database on startup if it's empty
def seed_demo_data():
    """Seed demo data if database is empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            print("Seeding demo data...")
            from seed import seed
            db.close()
            seed()
            print("✓ Demo data seeded")
        else:
            print("✓ Database already has data")
    except Exception as e:
        print(f"✗ Error seeding demo data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            db.close()
        except:
            pass

seed_demo_data()

# Seed system defaults (idempotent – only adds missing entries)
def seed_system_defaults():
    """Seed system defaults like branches, payment methods, etc."""
    from app.seed_defaults import seed_all_defaults
    db = SessionLocal()
    try:
        print("Seeding system defaults...")
        seed_all_defaults(db)
        db.commit()
        print("✓ System defaults seeded")
    except Exception as e:
        print(f"✗ Error seeding defaults: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

seed_system_defaults()

app = FastAPI(
    title=settings.app_name,
    description="Operative Steuerung für Lohnbüros – Addison Operations Manager",
    version="1.0.0",
)

# CORS
# CORS_ORIGINS kann als kommaseparierte Liste gesetzt werden, z.B.:
#   CORS_ORIGINS=https://aom-frontend.up.railway.app,http://localhost:5173
_raw = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
_origins = [o.strip() for o in _raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(mandanten.router)
app.include_router(workflows.router)
app.include_router(tickets.router)
app.include_router(dokumente.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
app.include_router(email_templates.router)
app.include_router(admin.router)
app.include_router(fristen.router)
app.include_router(schritt_typen.router)
app.include_router(reporting.router)
app.include_router(global_events.router)

# Serve uploaded files
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
