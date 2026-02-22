from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app import legacy_main
from app.models import User
from app.schemas import AuthOut, ForgotPasswordIn, LoginIn, ResetPasswordIn, SignupIn, UpdateMeIn, UserOut

router = APIRouter()


@router.post("/api/auth/login", response_model=AuthOut)
def login(payload: LoginIn, request: Request, db: Session = Depends(legacy_main.get_db)):
    return legacy_main.login(payload, request, db)


@router.post("/api/auth/signup", response_model=AuthOut)
def signup(payload: SignupIn, db: Session = Depends(legacy_main.get_db)):
    return legacy_main.signup(payload, db)


@router.post("/api/auth/forgot-password")
def forgot_password(payload: ForgotPasswordIn, request: Request, db: Session = Depends(legacy_main.get_db)):
    return legacy_main.forgot_password(payload, request, db)


@router.post("/api/auth/reset-password")
def reset_password(payload: ResetPasswordIn, db: Session = Depends(legacy_main.get_db)):
    return legacy_main.reset_password(payload, db)


@router.get("/api/auth/me", response_model=UserOut)
def me(db: Session = Depends(legacy_main.get_db), current_user: User = Depends(legacy_main.get_current_user_dep)):
    return legacy_main.me(db, current_user)


@router.put("/api/auth/me", response_model=UserOut)
def update_me(
    payload: UpdateMeIn,
    db: Session = Depends(legacy_main.get_db),
    current_user: User = Depends(legacy_main.get_current_user_dep),
):
    return legacy_main.update_me(payload, db, current_user)


# Expose legacy endpoint directly for correct UploadFile handling.
router.add_api_route(
    "/api/auth/me/avatar",
    legacy_main.upload_my_avatar,
    methods=["POST"],
    response_model=UserOut,
)


router.add_api_route(
    "/api/auth/switch-tenant",
    legacy_main.switch_tenant,
    methods=["POST"],
    response_model=UserOut,
)
