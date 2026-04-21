from datetime import datetime, date
from typing import Optional, Literal
from pydantic import BaseModel, EmailStr, field_validator


# ─── Auth ────────────────────────────────────────────────────────────────────


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ─── User ───────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: Literal["developer", "manager", "tester", "devops"] = "developer"

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("password must be at least 8 characters")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[Literal["developer", "manager", "tester", "devops"]] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Team ────────────────────────────────────────────────────────────────────


class TeamCreate(BaseModel):
    name: str
    description: Optional[str] = None
    lead_id: Optional[int] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    lead_id: Optional[int] = None


class TeamMemberAdd(BaseModel):
    user_id: int


class TeamMemberOut(BaseModel):
    id: int
    user_id: int
    team_id: int
    joined_at: datetime
    user: UserOut

    model_config = {"from_attributes": True}


class TeamOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    lead_id: Optional[int]
    lead: Optional[UserOut]
    created_at: datetime
    members: list[TeamMemberOut] = []

    model_config = {"from_attributes": True}


# ─── Project ─────────────────────────────────────────────────────────────────


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    team_id: Optional[int] = None
    deadline: Optional[datetime] = None
    budget_hours: float = 0.0
    status: Literal["active", "completed", "on_hold"] = "active"


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    team_id: Optional[int] = None
    deadline: Optional[datetime] = None
    budget_hours: Optional[float] = None
    status: Optional[Literal["active", "completed", "on_hold"]] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str]
    team_id: Optional[int]
    deadline: Optional[datetime]
    budget_hours: float
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── ProjectMember ───────────────────────────────────────────────────────────


class ProjectMemberAdd(BaseModel):
    user_id: int
    member_role: str = "developer"


class ProjectMemberOut(BaseModel):
    id: int
    user_id: int
    project_id: int
    member_role: str
    joined_at: datetime
    user: UserOut

    model_config = {"from_attributes": True}


# ─── Report ──────────────────────────────────────────────────────────────────


class ReportCreate(BaseModel):
    user_id: int
    project_id: int
    report_date: date
    hours_spent: float
    comment: Optional[str] = None
    category: Literal["dev", "devops", "review", "bugfix", "meeting", "other"] = "other"

    @field_validator("hours_spent")
    @classmethod
    def hours_must_be_positive(cls, v: float) -> float:
        if v <= 0 or v > 24:
            raise ValueError("hours_spent must be between 0 and 24")
        return v


class ReportUpdate(BaseModel):
    hours_spent: Optional[float] = None
    comment: Optional[str] = None
    category: Optional[
        Literal["dev", "devops", "review", "bugfix", "meeting", "other"]
    ] = None


class ReportOut(BaseModel):
    id: int
    user_id: int
    project_id: int
    report_date: date
    hours_spent: float
    comment: Optional[str]
    category: str
    created_at: datetime
    user: UserOut

    model_config = {"from_attributes": True}


# ─── Issue ───────────────────────────────────────────────────────────────────


class IssueCreate(BaseModel):
    project_id: int
    assignee_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: Literal["open", "in_progress", "review", "closed"] = "open"
    issue_type: Literal["bug", "feature", "task", "epic"] = "task"
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    story_points: int = 1
    external_id: Optional[str] = None
    external_source: Optional[Literal["gitlab", "jira"]] = None


class IssueUpdate(BaseModel):
    assignee_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["open", "in_progress", "review", "closed"]] = None
    issue_type: Optional[Literal["bug", "feature", "task", "epic"]] = None
    priority: Optional[Literal["low", "medium", "high", "critical"]] = None
    story_points: Optional[int] = None


class IssueOut(BaseModel):
    id: int
    project_id: int
    assignee_id: Optional[int]
    title: str
    description: Optional[str]
    status: str
    issue_type: str
    priority: str
    story_points: int
    external_id: Optional[str]
    external_source: Optional[str]
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    assignee: Optional[UserOut]

    model_config = {"from_attributes": True}


# ─── GitLab / Jira Sync ──────────────────────────────────────────────────────


class GitLabIssuePayload(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    state: str
    labels: list[str] = []
    assignee: Optional[dict] = None


class GitLabSyncPayload(BaseModel):
    project_id: int
    issues: list[GitLabIssuePayload]


class JiraIssuePayload(BaseModel):
    key: str
    summary: str
    description: Optional[str] = None
    status: str
    issuetype: str
    priority: Optional[str] = None
    assignee: Optional[dict] = None


class JiraSyncPayload(BaseModel):
    project_id: int
    issues: list[JiraIssuePayload]


class SyncResult(BaseModel):
    created: int
    updated: int
    total: int


# ─── Analytics / Dashboard ───────────────────────────────────────────────────


class ProgressOut(BaseModel):
    total_issues: int
    closed_issues: int
    open_issues: int
    progress_pct: float
    estimated_completion: Optional[datetime]
    days_until_deadline: Optional[int]
    on_track: Optional[bool]


class VelocityPoint(BaseModel):
    week_start: date
    closed_issues: int
    story_points_closed: int


class WorkloadOut(BaseModel):
    user_id: int
    user_name: str
    weekly_hours: float
    at_risk: bool
    risk_reason: Optional[str]
    open_issues_count: int


class StaleIssueOut(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    assignee_name: Optional[str]
    days_stale: int


class DashboardOut(BaseModel):
    project_id: int
    project_name: str
    project_status: str
    budget_hours: float
    spent_hours: float
    budget_utilization_pct: float
    progress: ProgressOut
    velocity: list[VelocityPoint]
    stale_issues: list[StaleIssueOut]
    member_workloads: list[WorkloadOut]
    issues_by_type: dict[str, int]
    issues_by_priority: dict[str, int]
    hours_by_category: dict[str, float]
