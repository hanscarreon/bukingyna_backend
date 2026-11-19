import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.core.security import validate_password_rules

PH_LOCAL = re.compile(r"^\d{10}$")


class RegisterEmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        err = validate_password_rules(v)
        if err:
            raise ValueError(err)
        return v

    @model_validator(mode="after")
    def passwords_match(self) -> "RegisterEmailIn":
        if self.password != self.confirm_password:
            raise ValueError("confirm_password must match password")
        return self


class LoginEmailIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str
    client: Literal["mobile", "admin"] = "mobile"
    device_id: str = Field(default="unknown", max_length=128)


class ForgotPasswordIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr


class MobileStartIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_number: str = Field(min_length=10, max_length=10)
    device_id: str = Field(default="unknown", max_length=128)

    @field_validator("local_number")
    @classmethod
    def ph_digits(cls, v: str) -> str:
        if not PH_LOCAL.match(v):
            raise ValueError("Mobile number must be exactly 10 digits (PH)")
        return v


class MobileVerifyOtpIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_number: str = Field(min_length=10, max_length=10)
    otp: str = Field(min_length=4, max_length=8)
    device_id: str = Field(default="unknown", max_length=128)


class MobileSetPinIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_number: str = Field(min_length=10, max_length=10)
    pin: str = Field(min_length=6, max_length=6)
    otp_proof: str | None = None
    device_id: str = Field(default="unknown", max_length=128)

    @field_validator("pin")
    @classmethod
    def six_digits(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 6:
            raise ValueError("PIN must be exactly 6 digits")
        return v


class MobilePinLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    local_number: str = Field(min_length=10, max_length=10)
    pin: str = Field(min_length=6, max_length=6)
    device_id: str = Field(default="unknown", max_length=128)


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str
    tier: str | None = None
    email_verified: bool = False
    requires_pin_setup: bool = False
    message: str | None = None
    # DEV only — never populated in uat/prod
    dev_otp: str | None = None


class ProfileOut(BaseModel):
    id: str
    email: str | None
    phone_e164: str | None
    role: str
    tier: str
    email_verified: bool
    is_blocked: bool


class MessageOut(BaseModel):
    message: str
    locked: bool = False
    redirect: str | None = None
    dev_otp: str | None = None
