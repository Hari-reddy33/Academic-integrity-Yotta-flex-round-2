from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import create_access_token, get_current_user, verify_password
from app.models import User

router = APIRouter(prefix="/auth", tags=["authentication"])


def user_summary(user: User):
    return {"id": user.id, "email": user.email, "full_name": user.full_name, "role": user.role}


@router.post("/token")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == form.username, User.active.is_(True)))
    if user is None or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user), "token_type": "bearer"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return user_summary(user)
