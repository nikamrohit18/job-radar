import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # must run before importing agent modules (Anthropic client reads API key on init)

from api.routes import applications, coverletter, jobs, optimize, prep, users
from db.session import init_db

app = FastAPI(
    title="job-radar API",
    version="2.0.0",
    description="AI-powered job scoring and application tracking API",
)

_allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


# --- routes ---
app.include_router(jobs.router,         prefix="/jobs",         tags=["jobs"])
app.include_router(applications.router, prefix="/applications", tags=["applications"])
app.include_router(coverletter.router,  prefix="/jobs",         tags=["cover-letter"])
app.include_router(prep.router,         prefix="/jobs",         tags=["interview-prep"])
app.include_router(optimize.router,     prefix="/optimize",     tags=["optimize"])
app.include_router(users.router,        prefix="/users",        tags=["users"])


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}
