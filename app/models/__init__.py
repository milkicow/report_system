from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Date,
    ForeignKey,
    Enum as SAEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        SAEnum("developer", "manager", "tester", "devops", name="user_role"),
        default="developer",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reports: Mapped[list["Report"]] = relationship("Report", back_populates="user")
    issues: Mapped[list["Issue"]] = relationship("Issue", back_populates="assignee")
    memberships: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="user"
    )
    team_memberships: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="user"
    )
    led_teams: Mapped[list["Team"]] = relationship(
        "Team", foreign_keys="Team.lead_id", back_populates="lead"
    )


class Team(Base):
    __tablename__ = "teams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(
        String(200), unique=True, nullable=False, index=True
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    lead_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    lead: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[lead_id], back_populates="led_teams"
    )
    members: Mapped[list["TeamMember"]] = relationship(
        "TeamMember", back_populates="team"
    )
    projects: Mapped[list["Project"]] = relationship("Project", back_populates="team")


class TeamMember(Base):
    __tablename__ = "team_members"
    __table_args__ = (UniqueConstraint("team_id", "user_id", name="uq_team_user"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    team_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    team_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True
    )
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    budget_hours: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(
        SAEnum("active", "completed", "on_hold", name="project_status"),
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    team: Mapped[Optional["Team"]] = relationship("Team", back_populates="projects")
    issues: Mapped[list["Issue"]] = relationship("Issue", back_populates="project")
    reports: Mapped[list["Report"]] = relationship("Report", back_populates="project")
    members: Mapped[list["ProjectMember"]] = relationship(
        "ProjectMember", back_populates="project"
    )


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE")
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    member_role: Mapped[str] = mapped_column(String(50), default="developer")
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="memberships")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE")
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE")
    )
    report_date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_spent: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(
        SAEnum(
            "dev",
            "devops",
            "review",
            "bugfix",
            "meeting",
            "other",
            name="report_category",
        ),
        default="other",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="reports")
    project: Mapped["Project"] = relationship("Project", back_populates="reports")


class Issue(Base):
    __tablename__ = "issues"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE")
    )
    assignee_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("open", "in_progress", "review", "closed", name="issue_status"),
        default="open",
    )
    issue_type: Mapped[str] = mapped_column(
        SAEnum("bug", "feature", "task", "epic", name="issue_type"), default="task"
    )
    priority: Mapped[str] = mapped_column(
        SAEnum("low", "medium", "high", "critical", name="issue_priority"),
        default="medium",
    )
    story_points: Mapped[int] = mapped_column(Integer, default=1)
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_source: Mapped[Optional[str]] = mapped_column(
        SAEnum("gitlab", "jira", name="external_source"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="issues")
    assignee: Mapped[Optional["User"]] = relationship("User", back_populates="issues")
