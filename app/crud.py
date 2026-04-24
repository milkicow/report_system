"""CRUD helpers — all database read/write operations for every resource."""

from datetime import datetime, date, timezone
from typing import Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.auth import hash_password
from app.models import User, Project, ProjectMember, Report, Issue, Team, TeamMember
from app.schemas import (
    UserCreate,
    UserUpdate,
    ProjectCreate,
    ProjectUpdate,
    ProjectMemberAdd,
    ReportCreate,
    ReportUpdate,
    IssueCreate,
    IssueUpdate,
    TeamCreate,
    TeamUpdate,
    TeamMemberAdd,
)


# ─── Users ───────────────────────────────────────────────────────────────────


def get_user(db: Session, user_id: int) -> User:
    """Return a user by ID or raise 404."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


def get_users(
    db: Session, name: Optional[str] = None, skip: int = 0, limit: int = 100
) -> list[User]:
    """Return a paginated list of users, optionally filtered by name substring."""
    q = db.query(User)
    if name:
        q = q.filter(User.name.ilike(f"%{name}%"))
    return q.offset(skip).limit(limit).all()


def create_user(db: Session, data: UserCreate) -> User:
    """Create and persist a new user; raise 409 if the email already exists."""
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    fields = data.model_dump()
    fields["password_hash"] = hash_password(fields.pop("password"))
    user = User(**fields)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, user_id: int, data: UserUpdate) -> User:
    """Apply partial updates to an existing user and return the updated record."""
    user = get_user(db, user_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> None:
    """Delete a user by ID."""
    user = get_user(db, user_id)
    db.delete(user)
    db.commit()


# ─── Projects ────────────────────────────────────────────────────────────────


def get_project(db: Session, project_id: int) -> Project:
    """Return a project by ID or raise 404."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    return project


def get_projects(
    db: Session, skip: int = 0, limit: int = 100, status: Optional[str] = None
) -> list[Project]:
    """Return a paginated, optionally filtered list of projects."""
    q = db.query(Project)
    if status:
        q = q.filter(Project.status == status)
    return q.offset(skip).limit(limit).all()


def create_project(db: Session, data: ProjectCreate) -> Project:
    """Create and persist a new project."""
    project = Project(**data.model_dump())
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def update_project(db: Session, project_id: int, data: ProjectUpdate) -> Project:
    """Apply partial updates to an existing project and return the updated record."""
    project = get_project(db, project_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int) -> None:
    """Delete a project by ID."""
    project = get_project(db, project_id)
    db.delete(project)
    db.commit()


# ─── Project Members ─────────────────────────────────────────────────────────


def add_member(db: Session, project_id: int, data: ProjectMemberAdd) -> ProjectMember:
    """Add a user to a project; raise 409 if already a member."""
    get_project(db, project_id)
    get_user(db, data.user_id)
    existing = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == data.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409, detail="User already a member of this project"
        )
    member = ProjectMember(project_id=project_id, **data.model_dump())
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def get_members(db: Session, project_id: int) -> list[ProjectMember]:
    """Return all members of a project."""
    get_project(db, project_id)
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()


def remove_member(db: Session, project_id: int, user_id: int) -> None:
    """Remove a user from a project; raise 404 if they are not a member."""
    member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id, ProjectMember.user_id == user_id
        )
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this project")
    db.delete(member)
    db.commit()


# ─── Reports ─────────────────────────────────────────────────────────────────


def get_report(db: Session, report_id: int) -> Report:
    """Return a report by ID or raise 404."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report


def get_reports(
    db: Session,
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Report]:
    """Return a filtered, paginated list of reports ordered by date descending."""
    q = db.query(Report)
    if project_id:
        q = q.filter(Report.project_id == project_id)
    if user_id:
        q = q.filter(Report.user_id == user_id)
    if date_from:
        q = q.filter(Report.report_date >= date_from)
    if date_to:
        q = q.filter(Report.report_date <= date_to)
    return q.order_by(Report.report_date.desc()).offset(skip).limit(limit).all()


def create_report(db: Session, data: ReportCreate, user_id: int) -> Report:
    """Create and persist a new daily report after validating project."""
    get_project(db, data.project_id)
    report = Report(user_id=user_id, **data.model_dump())
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def update_report(db: Session, report_id: int, data: ReportUpdate) -> Report:
    """Apply partial updates to an existing report."""
    report = get_report(db, report_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(report, field, value)
    db.commit()
    db.refresh(report)
    return report


def delete_report(db: Session, report_id: int) -> None:
    """Delete a report by ID."""
    report = get_report(db, report_id)
    db.delete(report)
    db.commit()


# ─── Issues ──────────────────────────────────────────────────────────────────


def get_issue(db: Session, issue_id: int) -> Issue:
    """Return an issue by ID or raise 404."""
    issue = db.query(Issue).filter(Issue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=404, detail=f"Issue {issue_id} not found")
    return issue


def get_issues(
    db: Session,
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = None,
    issue_type: Optional[str] = None,
    priority: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Issue]:
    """Return a filtered, paginated list of issues ordered by creation date descending."""
    q = db.query(Issue)
    if project_id:
        q = q.filter(Issue.project_id == project_id)
    if assignee_id:
        q = q.filter(Issue.assignee_id == assignee_id)
    if status:
        q = q.filter(Issue.status == status)
    if issue_type:
        q = q.filter(Issue.issue_type == issue_type)
    if priority:
        q = q.filter(Issue.priority == priority)
    return q.order_by(Issue.created_at.desc()).offset(skip).limit(limit).all()


def create_issue(db: Session, data: IssueCreate) -> Issue:
    """Create and persist a new issue, auto-setting closed_at when status is closed."""
    get_project(db, data.project_id)
    if data.assignee_id:
        get_user(db, data.assignee_id)
    issue = Issue(**data.model_dump())
    if issue.status == "closed" and not issue.closed_at:
        issue.closed_at = datetime.now(timezone.utc)
    db.add(issue)
    db.commit()
    db.refresh(issue)
    return issue


def update_issue(db: Session, issue_id: int, data: IssueUpdate) -> Issue:
    """Apply partial updates to an issue, managing closed_at based on status transitions."""
    issue = get_issue(db, issue_id)
    updates = data.model_dump(exclude_none=True)

    if updates.get("status") == "closed" and issue.status != "closed":
        issue.closed_at = datetime.now(timezone.utc)
    elif updates.get("status") and updates["status"] != "closed":
        issue.closed_at = None

    issue.updated_at = datetime.now(timezone.utc)
    for field, value in updates.items():
        setattr(issue, field, value)
    db.commit()
    db.refresh(issue)
    return issue


def delete_issue(db: Session, issue_id: int) -> None:
    """Delete an issue by ID."""
    issue = get_issue(db, issue_id)
    db.delete(issue)
    db.commit()


# ─── Teams ───────────────────────────────────────────────────────────────────


def get_team(db: Session, team_id: int) -> Team:
    """Return a team by ID or raise 404."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail=f"Team {team_id} not found")
    return team


def get_teams(db: Session, skip: int = 0, limit: int = 100) -> list[Team]:
    """Return a paginated list of all teams."""
    return db.query(Team).offset(skip).limit(limit).all()


def create_team(db: Session, data: TeamCreate) -> Team:
    """Create and persist a new team; raise 409 if the name already exists."""
    existing = db.query(Team).filter(Team.name == data.name).first()
    if existing:
        raise HTTPException(
            status_code=409, detail=f"Team '{data.name}' already exists"
        )
    if data.lead_id:
        get_user(db, data.lead_id)
    team = Team(**data.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


def update_team(db: Session, team_id: int, data: TeamUpdate) -> Team:
    """Apply partial updates to an existing team."""
    team = get_team(db, team_id)
    updates = data.model_dump(exclude_none=True)
    if "lead_id" in updates and updates["lead_id"]:
        get_user(db, updates["lead_id"])
    for field, value in updates.items():
        setattr(team, field, value)
    db.commit()
    db.refresh(team)
    return team


def delete_team(db: Session, team_id: int) -> None:
    """Delete a team by ID."""
    team = get_team(db, team_id)
    db.delete(team)
    db.commit()


def add_team_member(db: Session, team_id: int, data: TeamMemberAdd) -> TeamMember:
    """Add a user to a team; raise 409 if already a member."""
    get_team(db, team_id)
    get_user(db, data.user_id)
    existing = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == data.user_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="User already in this team")
    member = TeamMember(team_id=team_id, user_id=data.user_id)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_team_member(db: Session, team_id: int, user_id: int) -> None:
    """Remove a user from a team; raise 404 if they are not a member."""
    member = (
        db.query(TeamMember)
        .filter(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        .first()
    )
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in this team")
    db.delete(member)
    db.commit()
