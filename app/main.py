"""FastAPI application factory: registers routers and creates DB tables on startup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routers import users, projects, reports, issues, analytics, teams, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Internal Reporting System",
    description="""
## Internal Reporting and Project Management System

REST API for tracking development progress, logging work hours,
and synchronizing tasks from GitLab/Jira.

### Key Features
- **Teams** — permanent developer groups with a lead
- **Users** — roles: developer / manager / tester / devops
- **Projects** — linked to a team, with deadline and hour budget
- **Reports** — daily work logs by hours and category
- **Issues** — tasks with priorities, statuses, story points
- **Analytics** — dashboard, velocity, deadline forecast, risk detection
- **Sync** — import issues from GitLab and Jira
    """,
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(teams.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(reports.router)
app.include_router(issues.router)
app.include_router(analytics.router)


@app.get("/", tags=["Root"])
def root():
    """Return service metadata for health checks and discovery."""
    return {
        "service": "Internal Reporting System",
        "version": "1.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }
