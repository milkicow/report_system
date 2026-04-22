"""Teams router — CRUD endpoints for teams and team membership."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import TeamCreate, TeamUpdate, TeamOut, TeamMemberAdd, TeamMemberOut
from app import crud

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/", response_model=list[TeamOut])
def list_teams(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Return a paginated list of all teams."""
    return crud.get_teams(db, skip=skip, limit=limit)


@router.post("/", response_model=TeamOut, status_code=201)
def create_team(
    data: TeamCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Create a new team (requires authentication)."""
    return crud.create_team(db, data)


@router.get("/{team_id}", response_model=TeamOut)
def get_team(team_id: int, db: Session = Depends(get_db)):
    """Return a single team by ID."""
    return crud.get_team(db, team_id)


@router.patch("/{team_id}", response_model=TeamOut)
def update_team(
    team_id: int,
    data: TeamUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Partially update a team (requires authentication)."""
    return crud.update_team(db, team_id, data)


@router.delete("/{team_id}", status_code=204)
def delete_team(
    team_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Delete a team by ID (requires authentication)."""
    crud.delete_team(db, team_id)


@router.post("/{team_id}/members", response_model=TeamMemberOut, status_code=201)
def add_member(
    team_id: int,
    data: TeamMemberAdd,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Add a user to a team (requires authentication)."""
    return crud.add_team_member(db, team_id, data)


@router.delete("/{team_id}/members/{user_id}", status_code=204)
def remove_member(
    team_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Remove a user from a team (requires authentication)."""
    crud.remove_team_member(db, team_id, user_id)
