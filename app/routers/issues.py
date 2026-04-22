from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import IssueCreate, IssueUpdate, IssueOut
from app import crud

router = APIRouter(prefix="/issues", tags=["Issues"])


@router.get("/", response_model=list[IssueOut])
def list_issues(
    project_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    status: Optional[str] = Query(
        None, enum=["open", "in_progress", "review", "closed"]
    ),
    issue_type: Optional[str] = Query(None, enum=["bug", "feature", "task", "epic"]),
    priority: Optional[str] = Query(None, enum=["low", "medium", "high", "critical"]),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.get_issues(
        db,
        project_id=project_id,
        assignee_id=assignee_id,
        status=status,
        issue_type=issue_type,
        priority=priority,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=IssueOut, status_code=201)
def create_issue(
    data: IssueCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.create_issue(db, data)


@router.get("/{issue_id}", response_model=IssueOut)
def get_issue(issue_id: int, db: Session = Depends(get_db)):
    return crud.get_issue(db, issue_id)


@router.patch("/{issue_id}", response_model=IssueOut)
def update_issue(
    issue_id: int,
    data: IssueUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.update_issue(db, issue_id, data)


@router.post("/{issue_id}/close", response_model=IssueOut)
def close_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.update_issue(db, issue_id, IssueUpdate(status="closed"))


@router.delete("/{issue_id}", status_code=204)
def delete_issue(
    issue_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    crud.delete_issue(db, issue_id)
