from sqlalchemy import Column, Integer, String, Text, DateTime
from .database import Base
from datetime import datetime

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender = Column(String, index=True) # "user" or "bot"
    text = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
