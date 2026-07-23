from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import httpx

from app.auth import hash_password, verify_password, create_access_token, CurrentUser
from app.config import get_settings
from app.database import get_db
from app.models import User
from app.schemas import (
    UserCreate,
    UserLogin,
    UserOut,
    TokenResponse,
    GoogleAuthRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


@router.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email.lower(),
        full_name=payload.full_name.strip(),
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return UserOut.model_validate(user)


@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    """Verify Google ID token via tokeninfo endpoint (works without client secret for ID tokens)."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://oauth2.googleapis.com/tokeninfo",
            params={"id_token": payload.credential},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail="Invalid Google credential")

    info = resp.json()
    if settings.google_client_id and info.get("aud") != settings.google_client_id:
        raise HTTPException(status_code=400, detail="Google audience mismatch")

    email = (info.get("email") or "").lower()
    google_id = info.get("sub")
    if not email or not google_id:
        raise HTTPException(status_code=400, detail="Google account missing email")

    user = db.query(User).filter((User.google_id == google_id) | (User.email == email)).first()
    if not user:
        user = User(
            email=email,
            full_name=info.get("name") or email.split("@")[0],
            google_id=google_id,
            avatar_url=info.get("picture"),
        )
        db.add(user)
    else:
        user.google_id = google_id
        if info.get("picture"):
            user.avatar_url = info.get("picture")
        if info.get("name") and not user.full_name:
            user.full_name = info.get("name")

    db.commit()
    db.refresh(user)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token, user=UserOut.model_validate(user))
