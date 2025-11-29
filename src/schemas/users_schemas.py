from pydantic import BaseModel, EmailStr
from typing import Optional


# -----------------------------
# LOGIN
# -----------------------------
class Login(BaseModel):
    email: EmailStr
    password: str

    class Config:
        orm_mode = True


# -----------------------------
# USER RESPONSE (GET / LIST)
# -----------------------------
class UserResponse(BaseModel):
    # id: str
    fullName: str
    email: EmailStr
    # role: str

    class Config:
        orm_mode = True


# -----------------------------
# CREATE NEW USER
# -----------------------------
class NewUser(BaseModel):
    fullName: str
    email: EmailStr
    password: str
    # role: str = "user"

    class Config:
        orm_mode = True


# -----------------------------
# UPDATE USER
# -----------------------------
class UpdateUser(BaseModel):
    fullName: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    role: Optional[str] = None

    class Config:
        orm_mode = True


# -----------------------------
# LOGIN RESPONSE WITH TOKENS
# -----------------------------
class LoginResponse(BaseModel):
    success: bool
    access_token: str
    refresh_token: str
    user: UserResponse
