import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bots = relationship("Bot", back_populates="owner")


class Bot(Base):
    __tablename__ = "bots"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    language = Column(String, nullable=False, default="python")
    entrypoint = Column(String, nullable=False, default="bot.py")
    token = Column(String, nullable=False)
    status = Column(String, default="stopped")
    bot_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="bots")
    processes = relationship("BotProcess", back_populates="bot")
    logs = relationship("Log", back_populates="bot")


class BotProcess(Base):
    __tablename__ = "bot_processes"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    pid = Column(Integer, nullable=True)
    status = Column(String, default="stopped")
    started_at = Column(DateTime, default=datetime.datetime.utcnow)
    stopped_at = Column(DateTime, nullable=True)

    bot = relationship("Bot", back_populates="processes")


class Log(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    bot_id = Column(Integer, ForeignKey("bots.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bot = relationship("Bot", back_populates="logs")
