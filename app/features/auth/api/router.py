from fastapi import APIRouter, Depends, HTTPException, status

from app.features.auth.api.deps import get_auth_use_cases, get_current_profile
from app.features.auth.data.models import Profile
from app.features.auth.data.schemas import (
    ForgotPasswordIn,
    LoginEmailIn,
    MessageOut,
    MobilePinLoginIn,
    MobileSetPinIn,
    MobileStartIn,
    MobileVerifyOtpIn,
    ProfileOut,
    RegisterEmailIn,
    TokenOut,
)
from app.features.auth.domain.use_cases import AuthUseCases

router = APIRouter(prefix="/auth", tags=["auth"])


def _map_error(exc: ValueError) -> HTTPException:
    msg = str(exc)
    if msg == "LOCKED_USER":
        return HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"message": "Account locked after 3 failed attempts.", "redirect": "forgot_password"},
        )
    if msg == "LOCKED_ADMIN":
        return HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={"message": "Admin account locked. Please contact us.", "redirect": "contact_us"},
        )
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)


@router.post("/email/register", response_model=TokenOut)
def register_email(body: RegisterEmailIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> TokenOut:
    try:
        return uc.register_email(str(body.email), body.password)
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/email/login", response_model=TokenOut)
def login_email(body: LoginEmailIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> TokenOut:
    try:
        return uc.login_email(str(body.email), body.password, body.client, body.device_id)
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/email/forgot-password", response_model=MessageOut)
def forgot_password(body: ForgotPasswordIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> MessageOut:
    result = uc.forgot_password(str(body.email))
    return MessageOut(message=result["message"], redirect=result.get("redirect"))


@router.post("/mobile/start", response_model=MessageOut)
def mobile_start(body: MobileStartIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> MessageOut:
    try:
        result = uc.mobile_start(body.local_number, body.device_id)
        return MessageOut(message=result["message"], dev_otp=result.get("dev_otp"))
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/mobile/verify-otp", response_model=TokenOut)
def mobile_verify_otp(body: MobileVerifyOtpIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> TokenOut:
    try:
        return uc.mobile_verify_otp(body.local_number, body.otp, body.device_id)
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/mobile/set-pin", response_model=TokenOut)
def mobile_set_pin(body: MobileSetPinIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> TokenOut:
    try:
        return uc.mobile_set_pin(body.local_number, body.pin, body.device_id)
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/mobile/pin-login", response_model=TokenOut)
def mobile_pin_login(body: MobilePinLoginIn, uc: AuthUseCases = Depends(get_auth_use_cases)) -> TokenOut:
    try:
        return uc.mobile_pin_login(body.local_number, body.pin, body.device_id)
    except ValueError as e:
        raise _map_error(e) from e


@router.post("/logout", response_model=MessageOut)
def logout(
    profile: Profile = Depends(get_current_profile),
    uc: AuthUseCases = Depends(get_auth_use_cases),
) -> MessageOut:
    uc.logout(profile.id)
    return MessageOut(message="Logged out")


@router.get("/me", response_model=ProfileOut)
def me(profile: Profile = Depends(get_current_profile)) -> ProfileOut:
    return ProfileOut(
        id=profile.id,
        email=profile.email,
        phone_e164=profile.phone_e164,
        role=profile.role,
        tier=profile.tier,
        email_verified=profile.email_verified,
        is_blocked=profile.is_blocked,
    )
