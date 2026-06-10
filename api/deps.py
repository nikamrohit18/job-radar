"""FastAPI dependencies — DB session and authenticated user."""
from datetime import datetime

from fastapi import Depends
from sqlalchemy.orm import Session

from api.auth import get_clerk_user_id
from db.models import User
from db.session import get_db


def get_current_user(
    clerk_id: str = Depends(get_clerk_user_id),
    db: Session = Depends(get_db),
) -> User:
    """Resolve the Clerk user ID to a DB user, creating the record on first login."""
    user = db.query(User).filter(User.clerk_id == clerk_id).first()
    if not user:
        user = User(clerk_id=clerk_id, created_at=datetime.utcnow())
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
