from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps import get_current_user, get_db
from api.schemas import UserOut, UserUpdateIn
from db import models as orm

router = APIRouter()


@router.get("/me", response_model=UserOut)
def get_me(
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    return UserOut(
        id=user.id,
        clerk_id=user.clerk_id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )


@router.patch("/me", response_model=UserOut)
def update_me(
    body: UserUpdateIn,
    db: Session = Depends(get_db),
    user: orm.User = Depends(get_current_user),
):
    if body.email is not None:
        user.email = body.email
    if body.name is not None:
        user.name = body.name
    db.commit()
    db.refresh(user)
    return UserOut(
        id=user.id,
        clerk_id=user.clerk_id,
        email=user.email,
        name=user.name,
        created_at=user.created_at,
    )
