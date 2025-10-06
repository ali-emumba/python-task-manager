from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.schemas.auth import Token
from app.services.auth_service import create_user, authenticate_user
from app.core.security import create_access_token
from app.core.logging import log_business_step
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, request: Request, db: Session = Depends(get_db)):
    log_business_step(
        "user_registration_start",
        {"email": user_in.email},
        request=request
    )
    
    try:
        log_business_step(
            "user_validation_start",
            {"email": user_in.email, "password_length": len(user_in.password)},
            request=request
        )
        
        user = create_user(db, user_in)
        
        log_business_step(
            "user_created_successfully",
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value
            },
            request=request,
            user_id=user.id
        )
        
        return UserRead.model_validate(user)
        
    except Exception as e:
        log_business_step(
            "user_registration_failed",
            {
                "email": user_in.email,
                "error": str(e),
                "error_type": type(e).__name__
            },
            request=request,
            level="error"
        )
        raise

@router.post("/login", response_model=Token)
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    log_business_step(
        "user_login_start",
        {"email": form_data.username},
        request=request
    )
    
    try:
        log_business_step(
            "user_authentication_start",
            {"email": form_data.username},
            request=request
        )
        
        user: User = authenticate_user(db, form_data.username, form_data.password)
        
        log_business_step(
            "user_authenticated_successfully",
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role.value
            },
            request=request,
            user_id=user.id
        )
        
        log_business_step(
            "jwt_token_generation_start",
            {"user_id": user.id},
            request=request,
            user_id=user.id
        )
        
        token = create_access_token({"sub": user.email})
        
        log_business_step(
            "user_login_completed",
            {
                "user_id": user.id,
                "email": user.email,
                "token_length": len(token)
            },
            request=request,
            user_id=user.id
        )
        
        return Token(access_token=token)
        
    except Exception as e:
        log_business_step(
            "user_login_failed",
            {
                "email": form_data.username,
                "error": str(e),
                "error_type": type(e).__name__
            },
            request=request,
            level="error"
        )
        raise
