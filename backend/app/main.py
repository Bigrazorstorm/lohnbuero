from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.config import settings
from app.database import Base, engine, run_migrations
from app.routers import auth, dashboard, dokumente, mandanten, tickets, users, workflows
from app.routers import audit, email_templates

# Create all tables (new ones)
Base.metadata.create_all(bind=engine)

# Safely migrate existing tables (add new columns)
run_migrations()

app = FastAPI(
    title=settings.app_name,
    description="Operative Steuerung für Lohnbüros – Addison Operations Manager",
    version="1.0.0",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
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

# Serve uploaded files
uploads_dir = "uploads"
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}
