"""
Analytics Service — algorithmic business logic:
  1. calculate_progress   — project progress + deadline forecast
  2. calculate_velocity   — team velocity per week
  3. detect_user_workload — employee overload detection
  4. detect_stale_issues  — find stuck issues
  5. get_dashboard        — project summary dashboard
"""

from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException

from app.models import User, Project, ProjectMember, Report, Issue
from app.schemas import (
    ProgressOut,
    VelocityPoint,
    WorkloadOut,
    StaleIssueOut,
    DashboardOut,
)

OVERLOAD_HOURS_PER_WEEK = 40.0  # overload threshold
STALE_DAYS_THRESHOLD = 5  # days without update before an issue is stale
VELOCITY_WEEKS = 6  # rolling window for velocity calculation


# ─── 1. Project progress ─────────────────────────────────────────────────────


def calculate_progress(db: Session, project_id: int) -> ProgressOut:
    """
    Algorithm:
    - Compute percentage of closed issues
    - Calculate average velocity (issues/week) over the last VELOCITY_WEEKS weeks
    - Forecast completion date: now + (open_issues / velocity)
    - Determine whether the project is on track for the deadline
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    issues = db.query(Issue).filter(Issue.project_id == project_id).all()

    total = len(issues)
    closed = sum(1 for i in issues if i.status == "closed")
    open_count = total - closed
    progress_pct = round(closed / total * 100, 1) if total > 0 else 0.0

    # average closed issues per week
    avg_velocity = _avg_weekly_velocity(db, project_id, weeks=VELOCITY_WEEKS)

    estimated_completion: Optional[datetime] = None
    if avg_velocity > 0 and open_count > 0:
        weeks_needed = open_count / avg_velocity
        estimated_completion = datetime.utcnow() + timedelta(
            weeks=weeks_needed
        )
    elif open_count == 0:
        estimated_completion = datetime.utcnow()

    days_until_deadline: Optional[int] = None
    on_track: Optional[bool] = None
    if project and project.deadline:
        delta = project.deadline - datetime.utcnow()
        days_until_deadline = delta.days
        if estimated_completion:
            on_track = estimated_completion <= project.deadline

    return ProgressOut(
        total_issues=total,
        closed_issues=closed,
        open_issues=open_count,
        progress_pct=progress_pct,
        estimated_completion=estimated_completion,
        days_until_deadline=days_until_deadline,
        on_track=on_track,
    )


# ─── 2. Velocity by week ─────────────────────────────────────────────────────


def calculate_velocity(
    db: Session, project_id: int, weeks: int = VELOCITY_WEEKS
) -> list[VelocityPoint]:
    """
    Algorithm:
    - Split the last `weeks` weeks into calendar windows (Mon-Sun)
    - Count closed issues and total story points per window
    - Return a time series (burndown-like data)
    """
    today = date.today()
    # start of the current week (Monday)
    start_of_week = today - timedelta(days=today.weekday())
    windows = []
    for i in range(weeks - 1, -1, -1):
        week_start = start_of_week - timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        windows.append((week_start, week_end))

    result = []
    for w_start, w_end in windows:
        closed_issues = (
            db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.status == "closed",
                func.date(Issue.closed_at) >= w_start,
                func.date(Issue.closed_at) <= w_end,
            )
            .all()
        )

        result.append(
            VelocityPoint(
                week_start=w_start,
                closed_issues=len(closed_issues),
                story_points_closed=sum(i.story_points for i in closed_issues),
            )
        )
    return result


def _avg_weekly_velocity(db: Session, project_id: int, weeks: int) -> float:
    """Return average number of closed issues per week over the given window."""
    points = calculate_velocity(db, project_id, weeks=weeks)
    total_closed = sum(p.closed_issues for p in points)
    return total_closed / weeks if weeks > 0 else 0.0


# ─── 3. User workload ────────────────────────────────────────────────────────


def detect_user_workload(db: Session, user_id: int) -> WorkloadOut:
    """
    Algorithm:
    - Sum hours from reports over the last 7 days
    - Set at_risk = True if total > OVERLOAD_HOURS_PER_WEEK
    - Also count open issues assigned to the user
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    week_ago = date.today() - timedelta(days=7)

    reports = (
        db.query(Report)
        .filter(
            Report.user_id == user_id,
            Report.report_date >= week_ago,
        )
        .all()
    )
    weekly_hours = sum(r.hours_spent for r in reports)

    open_issues = (
        db.query(Issue)
        .filter(
            Issue.assignee_id == user_id,
            Issue.status.in_(["open", "in_progress", "review"]),
        )
        .count()
    )

    at_risk = weekly_hours > OVERLOAD_HOURS_PER_WEEK
    risk_reason: Optional[str] = None
    if at_risk:
        risk_reason = f"Logged {weekly_hours:.1f}h over 7 days (threshold: {OVERLOAD_HOURS_PER_WEEK}h)"

    return WorkloadOut(
        user_id=user_id,
        user_name=user.name if user else "Unknown",
        weekly_hours=round(weekly_hours, 1),
        at_risk=at_risk,
        risk_reason=risk_reason,
        open_issues_count=open_issues,
    )


# ─── 4. Stale issues ─────────────────────────────────────────────────────────


def detect_stale_issues(
    db: Session, project_id: int, stale_days: int = STALE_DAYS_THRESHOLD
) -> list[StaleIssueOut]:
    """
    Algorithm:
    - Find issues in in_progress/review whose updated_at is older than stale_days
    - Sort by staleness (days without update, descending)
    """
    threshold = datetime.utcnow() - timedelta(days=stale_days)
    stale = (
        db.query(Issue)
        .filter(
            Issue.project_id == project_id,
            Issue.status.in_(["in_progress", "review"]),
            Issue.updated_at <= threshold,
        )
        .all()
    )

    result = []
    for issue in stale:
        days_stale = (datetime.utcnow() - issue.updated_at).days
        result.append(
            StaleIssueOut(
                id=issue.id,
                title=issue.title,
                status=issue.status,
                priority=issue.priority,
                assignee_name=issue.assignee.name if issue.assignee else None,
                days_stale=days_stale,
            )
        )

    return sorted(result, key=lambda x: x.days_stale, reverse=True)


# ─── 5. Dashboard ────────────────────────────────────────────────────────────


def get_dashboard(db: Session, project_id: int) -> DashboardOut:
    """
    Aggregate all project metrics into a single object:
    - Overall progress and forecast
    - Velocity per week
    - Stale issues
    - Workload per member
    - Issue distribution by type/priority
    - Hour distribution by category
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # core metrics
    progress = calculate_progress(db, project_id)
    velocity = calculate_velocity(db, project_id)
    stale = detect_stale_issues(db, project_id)

    # budget utilization
    spent_hours = (
        db.query(func.sum(Report.hours_spent))
        .filter(Report.project_id == project_id)
        .scalar()
        or 0.0
    )
    budget_util = (
        round(spent_hours / project.budget_hours * 100, 1)
        if project.budget_hours > 0
        else 0.0
    )

    # member workloads
    members = (
        db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    )
    member_workloads = [detect_user_workload(db, m.user_id) for m in members]

    # issue distribution by type and priority
    issues_by_type: dict[str, int] = defaultdict(int)
    issues_by_priority: dict[str, int] = defaultdict(int)
    for issue in db.query(Issue).filter(Issue.project_id == project_id).all():
        issues_by_type[issue.issue_type] += 1
        issues_by_priority[issue.priority] += 1

    # hour distribution by category
    hours_by_category: dict[str, float] = defaultdict(float)
    for report in db.query(Report).filter(Report.project_id == project_id).all():
        hours_by_category[report.category] += report.hours_spent

    return DashboardOut(
        project_id=project_id,
        project_name=project.name,
        project_status=project.status,
        budget_hours=project.budget_hours,
        spent_hours=round(spent_hours, 1),
        budget_utilization_pct=budget_util,
        progress=progress,
        velocity=velocity,
        stale_issues=stale,
        member_workloads=member_workloads,
        issues_by_type=dict(issues_by_type),
        issues_by_priority=dict(issues_by_priority),
        hours_by_category={k: round(v, 1) for k, v in hours_by_category.items()},
    )


# ─── 6. GitLab / Jira sync ───────────────────────────────────────────────────


def _gitlab_state_to_status(state: str) -> str:
    return "closed" if state == "closed" else "open"


def _jira_status_to_status(jira_status: str) -> str:
    mapping = {
        "To Do": "open",
        "In Progress": "in_progress",
        "In Review": "review",
        "Done": "closed",
    }
    return mapping.get(jira_status, "open")


def _jira_type_to_type(jira_type: str) -> str:
    mapping = {
        "Bug": "bug",
        "Story": "feature",
        "Task": "task",
        "Epic": "epic",
    }
    return mapping.get(jira_type, "task")


def _jira_priority_to_priority(jira_priority: Optional[str]) -> str:
    mapping = {
        "Blocker": "critical",
        "Critical": "critical",
        "Major": "high",
        "Minor": "medium",
        "Trivial": "low",
    }
    return mapping.get(jira_priority or "", "medium")


def sync_gitlab_issues(db: Session, project_id: int, payloads: list) -> dict:
    """Upsert issues from a GitLab webhook payload."""
    created, updated = 0, 0
    for payload in payloads:
        existing = (
            db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.external_id == str(payload.id),
                Issue.external_source == "gitlab",
            )
            .first()
        )

        new_status = _gitlab_state_to_status(payload.state)
        if existing:
            existing.title = payload.title
            existing.description = payload.description
            existing.status = new_status
            existing.updated_at = datetime.utcnow()
            if new_status == "closed" and not existing.closed_at:
                existing.closed_at = datetime.utcnow()
            updated += 1
        else:
            issue = Issue(
                project_id=project_id,
                title=payload.title,
                description=payload.description,
                status=new_status,
                issue_type="task",
                priority="medium",
                external_id=str(payload.id),
                external_source="gitlab",
                closed_at=datetime.utcnow()
                if new_status == "closed"
                else None,
            )
            db.add(issue)
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}


def sync_jira_issues(db: Session, project_id: int, payloads: list) -> dict:
    """Upsert issues from a Jira webhook payload."""
    created, updated = 0, 0
    for payload in payloads:
        existing = (
            db.query(Issue)
            .filter(
                Issue.project_id == project_id,
                Issue.external_id == payload.key,
                Issue.external_source == "jira",
            )
            .first()
        )

        new_status = _jira_status_to_status(payload.status)
        if existing:
            existing.title = payload.summary
            existing.description = payload.description
            existing.status = new_status
            existing.issue_type = _jira_type_to_type(payload.issuetype)
            existing.priority = _jira_priority_to_priority(payload.priority)
            existing.updated_at = datetime.utcnow()
            if new_status == "closed" and not existing.closed_at:
                existing.closed_at = datetime.utcnow()
            updated += 1
        else:
            issue = Issue(
                project_id=project_id,
                title=payload.summary,
                description=payload.description,
                status=new_status,
                issue_type=_jira_type_to_type(payload.issuetype),
                priority=_jira_priority_to_priority(payload.priority),
                external_id=payload.key,
                external_source="jira",
                closed_at=datetime.utcnow()
                if new_status == "closed"
                else None,
            )
            db.add(issue)
            created += 1

    db.commit()
    return {"created": created, "updated": updated, "total": created + updated}
