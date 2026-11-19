import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_secret,
    verify_secret,
)
from app.features.auth.data.models import OtpChallenge, Profile
from app.features.auth.data.schemas import TokenOut
from app.features.auth.domain.notify import StubNotificationService
from app.features.auth.domain.roles import CUSTOMER, SUPER_ADMIN, is_admin_role
from app.features.auth.domain.strategies import AuthStrategy


def to_e164(local_number: str) -> str:
    return f"+63{local_number}"


def _aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


class AuthUseCases:
    def __init__(self, db: Session, auth: AuthStrategy) -> None:
        self.db = db
        self.auth = auth
        self.notify = StubNotificationService(db)
        self.settings = get_settings()

    def _tokens_for(self, profile: Profile, *, requires_pin_setup: bool = False, message: str | None = None) -> TokenOut:
        access = create_access_token(profile.id, profile.role, profile.tier)
        refresh = create_refresh_token(profile.id)
        return TokenOut(
            access_token=access,
            refresh_token=refresh,
            role=profile.role,
            tier=profile.tier,
            email_verified=profile.email_verified,
            requires_pin_setup=requires_pin_setup,
            message=message,
        )

    def _ensure_session(self, profile: Profile, device_id: str) -> None:
        if profile.active_session_id and profile.active_session_id != device_id:
            target = profile.email or profile.phone_e164 or profile.id
            self.notify.notify("email", target, f"Another device attempted login. device={device_id}")
            self.notify.notify("push", target, "concurrent_login_attempt")
            self.notify.notify("sms", target, "concurrent_login_attempt")
            raise ValueError("Account is active on another device. Sign out there first.")
        profile.active_session_id = device_id
        self.db.commit()

    def register_email(self, email: str, password: str) -> TokenOut:
        email_l = email.lower()
        existing = self.db.query(Profile).filter(Profile.email == email_l).first()
        if existing:
            if existing.is_blocked:
                raise ValueError("Email is blocked")
            raise ValueError("Email already used")

        if self.settings.auth_provider == "local":
            uid = self.auth.register_email(email_l, password)
            profile = self.db.query(Profile).filter(Profile.id == uid).first()
        else:
            uid = self.auth.register_email(email_l, password)
            profile = Profile(
                id=uid,
                email=email_l,
                role=CUSTOMER,
                tier="silver",
                password_hash=None,
            )
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        assert profile is not None
        return self._tokens_for(profile, message="Registered. Email verification optional.")

    def login_email(self, email: str, password: str, client: str, device_id: str) -> TokenOut:
        email_l = email.lower()
        profile = self.db.query(Profile).filter(Profile.email == email_l).first()

        if profile and profile.is_blocked:
            raise ValueError("Account is locked. Use forgot password or contact support.")

        try:
            uid = self.auth.login_email(email_l, password)
        except ValueError:
            if profile:
                profile.login_failures += 1
                if profile.login_failures >= 3:
                    profile.is_blocked = True
                    self.db.commit()
                    self.notify.notify("email", email_l, "account_locked_after_failed_logins")
                    if is_admin_role(profile.role) or client == "admin":
                        raise ValueError("LOCKED_ADMIN") from None
                    raise ValueError("LOCKED_USER") from None
                self.db.commit()
            raise ValueError("Invalid credentials") from None

        if not profile:
            # Supabase user without local profile yet
            profile = Profile(id=uid, email=email_l, role=CUSTOMER, tier="silver")
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)

        if client == "admin" and not is_admin_role(profile.role):
            raise ValueError("Not an admin account")

        profile.login_failures = 0
        self.db.commit()
        self._ensure_session(profile, device_id)
        return self._tokens_for(profile)

    def forgot_password(self, email: str) -> dict:
        email_l = email.lower()
        profile = self.db.query(Profile).filter(Profile.email == email_l).first()
        if profile and is_admin_role(profile.role):
            return {
                "message": "Admin accounts cannot reset password here. Please contact us.",
                "redirect": "contact_us",
            }
        self.auth.request_password_reset(email_l)
        if profile and profile.is_blocked and not is_admin_role(profile.role):
            # Unlock path via reset flow (docs default)
            profile.is_blocked = False
            profile.login_failures = 0
            self.db.commit()
        return {"message": "If the email exists, reset instructions were sent.", "redirect": "forgot_password"}

    def mobile_start(self, local_number: str, device_id: str) -> dict:
        phone = to_e164(local_number)
        profile = self.db.query(Profile).filter(Profile.phone_e164 == phone).first()
        if profile and profile.is_blocked:
            raise ValueError("Number is blocked")
        if profile and profile.otp_blocked_until and _aware(profile.otp_blocked_until) > datetime.now(UTC):
            raise ValueError("OTP temporarily blocked. Try again later.")
        if profile and profile.active_session_id and profile.active_session_id != device_id:
            self.notify.notify("sms", phone, "concurrent_login_attempt")
            raise ValueError("Number is signed in on another device.")

        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge = OtpChallenge(
            phone_e164=phone,
            code_hash=hash_secret(code),
            expires_at=datetime.now(UTC) + timedelta(minutes=10),
        )
        self.db.add(challenge)
        self.db.commit()

        out: dict = {"message": "OTP sent"}
        if self.settings.is_dev:
            out["dev_otp"] = code
        return out

    def mobile_verify_otp(self, local_number: str, otp: str, device_id: str) -> TokenOut:
        phone = to_e164(local_number)
        profile = self.db.query(Profile).filter(Profile.phone_e164 == phone).first()
        if profile and profile.is_blocked:
            raise ValueError("Number is blocked")
        if profile and profile.otp_blocked_until and _aware(profile.otp_blocked_until) > datetime.now(UTC):
            raise ValueError("OTP temporarily blocked for 24 hours")

        challenge = (
            self.db.query(OtpChallenge)
            .filter(OtpChallenge.phone_e164 == phone, OtpChallenge.consumed.is_(False))
            .order_by(OtpChallenge.expires_at.desc())
            .first()
        )
        if (
            not challenge
            or _aware(challenge.expires_at) < datetime.now(UTC)
            or not verify_secret(otp, challenge.code_hash)
        ):
            if profile:
                profile.otp_failures += 1
                if profile.otp_failures >= 3:
                    profile.otp_blocked_until = datetime.now(UTC) + timedelta(hours=24)
                    profile.otp_failures = 0
                self.db.commit()
            raise ValueError("Invalid OTP")

        challenge.consumed = True
        if not profile:
            profile = Profile(phone_e164=phone, role=CUSTOMER, tier="silver")
            self.db.add(profile)
        profile.otp_failures = 0
        self.db.commit()
        self.db.refresh(profile)

        needs_pin = profile.pin_hash is None
        if not needs_pin:
            self._ensure_session(profile, device_id)
        return self._tokens_for(profile, requires_pin_setup=needs_pin, message="OTP ok")

    def mobile_set_pin(self, local_number: str, pin: str, device_id: str) -> TokenOut:
        phone = to_e164(local_number)
        profile = self.db.query(Profile).filter(Profile.phone_e164 == phone).first()
        if not profile:
            raise ValueError("Complete OTP verification first")
        if profile.is_blocked:
            raise ValueError("Number is blocked")
        profile.pin_hash = hash_secret(pin)
        profile.pin_blocked = False
        profile.pin_failures = 0
        self.db.commit()
        self._ensure_session(profile, device_id)
        return self._tokens_for(profile, message="PIN set")

    def mobile_pin_login(self, local_number: str, pin: str, device_id: str) -> TokenOut:
        phone = to_e164(local_number)
        profile = self.db.query(Profile).filter(Profile.phone_e164 == phone).first()
        if not profile or not profile.pin_hash:
            raise ValueError("Invalid credentials")
        if profile.is_blocked:
            raise ValueError("Account blocked. Contact support.")
        if profile.pin_blocked:
            raise ValueError("PIN login blocked. Use OTP or forgot PIN.")

        if not verify_secret(pin, profile.pin_hash):
            profile.pin_failures += 1
            if profile.pin_failures >= 3:
                profile.pin_blocked = True
            self.db.commit()
            raise ValueError("Invalid PIN")

        profile.pin_failures = 0
        self.db.commit()
        self._ensure_session(profile, device_id)
        return self._tokens_for(profile)

    def logout(self, profile_id: str) -> None:
        profile = self.db.query(Profile).filter(Profile.id == profile_id).first()
        if profile:
            profile.active_session_id = None
            self.db.commit()

    def me(self, profile_id: str) -> Profile | None:
        return self.db.query(Profile).filter(Profile.id == profile_id).first()


def seed_superadmin(db: Session) -> None:
    settings = get_settings()
    if not settings.seed_superadmin_email or not settings.seed_superadmin_password:
        return
    email = settings.seed_superadmin_email.lower()
    existing = db.query(Profile).filter(Profile.email == email).first()
    if existing:
        return
    db.add(
        Profile(
            email=email,
            password_hash=hash_secret(settings.seed_superadmin_password),
            role=SUPER_ADMIN,
            tier="silver",
            email_verified=True,
        )
    )
    db.commit()
