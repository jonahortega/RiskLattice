"""Session management for anonymous users."""
from sqlmodel import Session, select
from app.models.models import User
from typing import Optional


def get_or_create_user(session: Session, session_id: str) -> User:
    """Get existing user by session_id or create a new guest user."""
    # Try to find existing user
    user_stmt = select(User).where(User.session_id == session_id)
    user = session.exec(user_stmt).first()
    
    if not user:
        # Create new guest user
        user = User(
            session_id=session_id,
            is_guest=True
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        print(f"Created new guest user with session_id: {session_id}")
    
    return user


def get_user_from_request(session: Session, session_id: Optional[str] = None) -> Optional[User]:
    """Get user from session_id. Returns None if session_id is not provided."""
    if not session_id:
        return None
    
    user_stmt = select(User).where(User.session_id == session_id)
    return session.exec(user_stmt).first()

