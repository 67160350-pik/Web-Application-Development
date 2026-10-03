from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import seed_data
from .database import Base, SessionLocal, engine
from .routers import auth, materials, parts, ships, trials, users

app = FastAPI(title="ShipForge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data.seed(db)
    finally:
        db.close()


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(parts.router)
app.include_router(materials.router)
app.include_router(ships.router)
app.include_router(trials.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
