"""Analytics router — dashboard, progress, velocity, workload, stale issues, and sync endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import (
    DashboardOut,
    ProgressOut,
    VelocityPoint,
    WorkloadOut,
    StaleIssueOut,
    SyncResult,
    GitLabSyncPayload,
    JiraSyncPayload,
)
from app.services.analytics import (
    get_dashboard,
    calculate_progress,
    calculate_velocity,
    detect_user_workload,
    detect_stale_issues,
    sync_gitlab_issues,
    sync_jira_issues,
)

router = APIRouter(tags=["Analytics"])


# ─── Project-level analytics ─────────────────────────────────────────────────


@router.get("/projects/{project_id}/dashboard", response_model=DashboardOut)
def project_dashboard(project_id: int, db: Session = Depends(get_db)):
    """Project dashboard: progress, velocity, workload, risks."""
    return get_dashboard(db, project_id)


@router.get("/projects/{project_id}/progress", response_model=ProgressOut)
def project_progress(project_id: int, db: Session = Depends(get_db)):
    """Project progress and estimated completion date."""
    return calculate_progress(db, project_id)


@router.get("/projects/{project_id}/velocity", response_model=list[VelocityPoint])
def project_velocity(
    project_id: int,
    weeks: int = 6,
    db: Session = Depends(get_db),
):
    """Team velocity — closed issues and story points per week."""
    return calculate_velocity(db, project_id, weeks=weeks)


@router.get("/projects/{project_id}/stale-issues", response_model=list[StaleIssueOut])
def project_stale_issues(
    project_id: int,
    stale_days: int = 5,
    db: Session = Depends(get_db),
):
    """Stale issues — stuck in in_progress/review without updates for N days."""
    return detect_stale_issues(db, project_id, stale_days=stale_days)


# ─── User-level analytics ────────────────────────────────────────────────────


@router.get("/users/{user_id}/workload", response_model=WorkloadOut)
def user_workload(user_id: int, db: Session = Depends(get_db)):
    """Employee workload over the last 7 days. at_risk flag set when > 40h."""
    return detect_user_workload(db, user_id)


# ─── Sync endpoints ──────────────────────────────────────────────────────────


@router.post("/projects/{project_id}/sync/gitlab", response_model=SyncResult)
def sync_gitlab(
    project_id: int,
    payload: GitLabSyncPayload,
    db: Session = Depends(get_db),
):
    """
    Sync issues from GitLab.
    Accepts a list of issues in GitLab webhook format and upserts them into the DB.
    """
    result = sync_gitlab_issues(db, project_id, payload.issues)
    return SyncResult(**result)


@router.post("/projects/{project_id}/sync/jira", response_model=SyncResult)
def sync_jira(
    project_id: int,
    payload: JiraSyncPayload,
    db: Session = Depends(get_db),
):
    """
    Sync issues from Jira.
    Accepts a list of issues in Jira webhook format and upserts them into the DB.
    """
    result = sync_jira_issues(db, project_id, payload.issues)
    return SyncResult(**result)
