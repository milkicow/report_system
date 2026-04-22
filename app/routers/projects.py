from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    ProjectOut,
    ProjectMemberAdd,
    ProjectMemberOut,
)
from app import crud

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get("/", response_model=list[ProjectOut])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = Query(None, enum=["active", "completed", "on_hold"]),
    db: Session = Depends(get_db),
):
    return crud.get_projects(db, skip=skip, limit=limit, status=status)


@router.post("/", response_model=ProjectOut, status_code=201)
def create_project(
    data: ProjectCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.create_project(db, data)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return crud.get_project(db, project_id)


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.update_project(db, project_id, data)


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    crud.delete_project(db, project_id)


# ─── Members ─────────────────────────────────────────────────────────────────


@router.get("/{project_id}/members", response_model=list[ProjectMemberOut])
def list_members(project_id: int, db: Session = Depends(get_db)):
    return crud.get_members(db, project_id)


@router.post("/{project_id}/members", response_model=ProjectMemberOut, status_code=201)
def add_member(
    project_id: int,
    data: ProjectMemberAdd,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return crud.add_member(db, project_id, data)


@router.delete("/{project_id}/members/{user_id}", status_code=204)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    crud.remove_member(db, project_id, user_id)
