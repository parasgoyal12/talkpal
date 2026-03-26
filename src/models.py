"""
Database models for the Study Companion Bot
"""
from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for storing user information"""
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    platform = Column(String, nullable=False)  # telegram, whatsapp
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    # User preferences
    preferences = Column(JSON, default={})

    # Relationships
    reminders = relationship("Reminder", back_populates="user", cascade="all, delete-orphan")
    study_sessions = relationship("StudySession", back_populates="user", cascade="all, delete-orphan")


class Reminder(Base):
    """Reminder model for storing user reminders"""
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    task_name = Column(String, nullable=False)
    reminder_time = Column(DateTime, nullable=False)
    status = Column(String, default="pending")  # pending, sent, cancelled
    created_at = Column(DateTime, default=datetime.utcnow)

    # Additional context
    context = Column(JSON, default={})

    # Relationship
    user = relationship("User", back_populates="reminders")


class StudySession(Base):
    """Study session model for tracking study history"""
    __tablename__ = "study_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    topic = Column(String, nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)

    # Session details
    notes = Column(Text, nullable=True)
    concepts_covered = Column(JSON, default=[])
    confidence_level = Column(Integer, nullable=True)  # 1-10

    # Relationship
    user = relationship("User", back_populates="study_sessions")


class KnowledgeLedger(Base):
    """Knowledge ledger for tracking what user has learned"""
    __tablename__ = "knowledge_ledger"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    concept = Column(String, nullable=False)

    # Learning tracking
    first_learned = Column(DateTime, default=datetime.utcnow)
    last_reviewed = Column(DateTime, default=datetime.utcnow)
    review_count = Column(Integer, default=0)
    confidence_score = Column(Integer, default=5)  # 1-10

    # Status
    status = Column(String, default="learning")  # learning, mastered, needs_review

    # Additional information
    notes = Column(Text, nullable=True)
    related_concepts = Column(JSON, default=[])
    sources = Column(JSON, default=[])


class ConversationLog(Base):
    """Log of all conversations for context"""
    __tablename__ = "conversation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    message = Column(Text, nullable=False)
    role = Column(String, nullable=False)  # user, assistant, system
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Metadata
    metadata = Column(JSON, default={})
