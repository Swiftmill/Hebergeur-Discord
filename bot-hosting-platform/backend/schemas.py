from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class BotBase(BaseModel):
    name: str
    language: str = "python"
    entrypoint: str = "bot.py"
    token: str


class BotCreate(BotBase):
    pass


class BotUpdate(BaseModel):
    name: Optional[str] = None
    language: Optional[str] = None
    entrypoint: Optional[str] = None
    token: Optional[str] = None


class BotOut(BaseModel):
    id: int
    name: str
    language: str
    entrypoint: str
    status: str
    created_at: datetime

    class Config:
        orm_mode = True


class BotDetail(BotOut):
    owner_id: int
    bot_path: str


class LogOut(BaseModel):
    id: int
    message: str
    created_at: datetime

    class Config:
        orm_mode = True
