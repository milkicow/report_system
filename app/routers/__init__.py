"""Router package — re-exports all sub-router modules."""

from app.routers import users, projects, reports, issues, analytics, teams

__all__ = ["users", "projects", "reports", "issues", "analytics", "teams"]
