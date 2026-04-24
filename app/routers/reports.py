"""Reports router — CRUD endpoints for daily work reports."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import ReportCreate, ReportUpdate, ReportOut
from app import crud

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=list[ReportOut])
def list_reports(
    project_id: Optional[int] = None,
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Return a filtered list of reports."""
    return crud.get_reports(
        db,
        project_id=project_id,
        user_id=user_id,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit,
    )


@router.post("/", response_model=ReportOut, status_code=201)
def create_report(
    data: ReportCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return crud.create_report(db, data, user_id=current_user.id)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(report_id: int, db: Session = Depends(get_db)):
    return crud.get_report(db, report_id)


@router.patch("/{report_id}", response_model=ReportOut)
def update_report(
    report_id: int,
    data: ReportUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.update_report(db, report_id, data)


@router.delete("/{report_id}", status_code=204)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    crud.delete_report(db, report_id)

