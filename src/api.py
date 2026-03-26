"""
FastAPI REST API for the Study Companion
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from loguru import logger
from src.agent import StudyCompanionAgent
from src.database import db
from src.models import User


app = FastAPI(
    title="Study Companion API",
    description="API for the Study Companion Bot",
    version="1.0.0"
)

agent = StudyCompanionAgent()


class ChatRequest(BaseModel):
    user_id: str
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None


class ChatResponse(BaseModel):
    response: str


class ProactiveMessageRequest(BaseModel):
    user_id: str
    context: Optional[Dict] = None


class ProactiveMessageResponse(BaseModel):
    message: str


class ReminderRequest(BaseModel):
    user_id: str
    task_name: str
    reminder_time: str
    context: Optional[Dict] = None


class ProgressRequest(BaseModel):
    user_id: str
    concept: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Study Companion API",
        "version": "1.0.0",
        "status": "running"
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the study companion agent
    """
    try:
        response = agent.chat(
            user_id=request.user_id,
            message=request.message,
            conversation_history=request.conversation_history
        )
        return ChatResponse(response=response)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/proactive-message", response_model=ProactiveMessageResponse)
async def generate_proactive_message(request: ProactiveMessageRequest):
    """
    Generate a proactive check-in message for a user
    """
    try:
        message = agent.generate_proactive_message(
            user_id=request.user_id,
            context=request.context
        )
        return ProactiveMessageResponse(message=message)
    except Exception as e:
        logger.error(f"Error generating proactive message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/reminder")
async def set_reminder(request: ReminderRequest):
    """
    Set a reminder for a user
    """
    try:
        result = agent.tools.set_reminder(
            user_id=request.user_id,
            task_name=request.task_name,
            reminder_time=request.reminder_time,
            context=request.context
        )
        return {"success": True, "message": result}
    except Exception as e:
        logger.error(f"Error setting reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/progress")
async def get_progress(request: ProgressRequest):
    """
    Get study progress for a user
    """
    try:
        progress = agent.tools.get_study_progress(
            user_id=request.user_id,
            concept=request.concept
        )
        return {"success": True, "progress": progress}
    except Exception as e:
        logger.error(f"Error getting progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/users")
async def list_users():
    """
    List all users
    """
    try:
        with db.get_session() as session:
            users = session.query(User).all()
            return {
                "users": [
                    {
                        "id": u.id,
                        "username": u.username,
                        "platform": u.platform,
                        "created_at": u.created_at.isoformat(),
                        "last_active": u.last_active.isoformat()
                    }
                    for u in users
                ]
            }
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    logger.info("Starting up API...")
    db.create_tables()
    logger.info("Database initialized")


if __name__ == "__main__":
    import uvicorn
    from config.settings import settings

    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_level=settings.log_level.lower()
    )
