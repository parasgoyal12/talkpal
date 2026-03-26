"""
Tools for the Azure AI Agent to use
"""
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from loguru import logger
from config.settings import settings
from src.database import db
from src.models import Reminder


class StudyCompanionTools:
    """Tools for the study companion agent"""

    @staticmethod
    def set_reminder(user_id: str, task_name: str, reminder_time: str, context: Optional[Dict] = None) -> str:
        """
        Schedule a reminder for the user to study a specific topic.

        Args:
            user_id: User identifier
            task_name: Name of the task to remind about
            reminder_time: ISO format datetime string (e.g., "2026-03-26T16:00:00")
            context: Optional additional context about the reminder

        Returns:
            Confirmation message
        """
        try:
            # Parse the reminder time
            reminder_dt = datetime.fromisoformat(reminder_time.replace('Z', '+00:00'))

            # Store in database
            with db.get_session() as session:
                reminder = Reminder(
                    user_id=user_id,
                    task_name=task_name,
                    reminder_time=reminder_dt,
                    context=context or {},
                    status="pending"
                )
                session.add(reminder)
                session.commit()

                # Trigger n8n webhook
                try:
                    payload = {
                        "user_id": user_id,
                        "task": task_name,
                        "time": reminder_time,
                        "reminder_id": reminder.id,
                        "context": context
                    }
                    response = requests.post(settings.n8n_webhook_url, json=payload, timeout=5)
                    response.raise_for_status()
                except Exception as e:
                    logger.warning(f"Failed to trigger n8n webhook: {e}")

                return f"Got it! I've set a reminder for '{task_name}' at {reminder_dt.strftime('%Y-%m-%d %H:%M')}."

        except Exception as e:
            logger.error(f"Error setting reminder: {e}")
            return f"Sorry, I couldn't set that reminder. Error: {str(e)}"

    @staticmethod
    def read_webpage(url: str) -> str:
        """
        Fetch and extract clean text content from a webpage.

        Args:
            url: The URL to read

        Returns:
            Clean text content from the webpage
        """
        try:
            # Send to n8n webhook for scraping if configured
            try:
                scraper_url = f"{settings.n8n_webhook_url}/scrape"
                response = requests.post(
                    scraper_url,
                    json={"url": url},
                    timeout=30
                )
                if response.status_code == 200:
                    return response.json().get("cleaned_text", "")
            except Exception:
                # Fallback to direct scraping
                pass

            # Direct scraping fallback
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Get text
            text = soup.get_text()

            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limit to reasonable length
            if len(text) > 10000:
                text = text[:10000] + "...(truncated)"

            return text

        except Exception as e:
            logger.error(f"Error reading webpage: {e}")
            return f"Sorry, I couldn't read that webpage. Error: {str(e)}"

    @staticmethod
    def update_knowledge_ledger(
        user_id: str,
        concept: str,
        status: str = "learning",
        confidence_score: Optional[int] = None,
        notes: Optional[str] = None
    ) -> str:
        """
        Update the knowledge ledger with information about what the user has learned.

        Args:
            user_id: User identifier
            concept: The concept being learned
            status: Status of learning (learning, mastered, needs_review)
            confidence_score: User's confidence level (1-10)
            notes: Optional notes about the concept

        Returns:
            Confirmation message
        """
        try:
            from src.models import KnowledgeLedger

            with db.get_session() as session:
                # Check if concept already exists
                ledger_entry = session.query(KnowledgeLedger).filter_by(
                    user_id=user_id,
                    concept=concept
                ).first()

                if ledger_entry:
                    # Update existing entry
                    ledger_entry.last_reviewed = datetime.utcnow()
                    ledger_entry.review_count += 1
                    if status:
                        ledger_entry.status = status
                    if confidence_score:
                        ledger_entry.confidence_score = confidence_score
                    if notes:
                        ledger_entry.notes = notes
                else:
                    # Create new entry
                    ledger_entry = KnowledgeLedger(
                        user_id=user_id,
                        concept=concept,
                        status=status,
                        confidence_score=confidence_score or 5,
                        notes=notes
                    )
                    session.add(ledger_entry)

                session.commit()
                return f"Knowledge ledger updated for '{concept}'. Status: {status}"

        except Exception as e:
            logger.error(f"Error updating knowledge ledger: {e}")
            return f"Sorry, I couldn't update the knowledge ledger. Error: {str(e)}"

    @staticmethod
    def get_study_progress(user_id: str, concept: Optional[str] = None) -> str:
        """
        Get the user's study progress for a specific concept or overall.

        Args:
            user_id: User identifier
            concept: Optional specific concept to check

        Returns:
            Progress information
        """
        try:
            from src.models import KnowledgeLedger

            with db.get_session() as session:
                if concept:
                    entry = session.query(KnowledgeLedger).filter_by(
                        user_id=user_id,
                        concept=concept
                    ).first()

                    if entry:
                        return (
                            f"Concept: {entry.concept}\n"
                            f"Status: {entry.status}\n"
                            f"Confidence: {entry.confidence_score}/10\n"
                            f"Reviewed {entry.review_count} times\n"
                            f"Last reviewed: {entry.last_reviewed.strftime('%Y-%m-%d')}"
                        )
                    else:
                        return f"No record found for '{concept}'"
                else:
                    entries = session.query(KnowledgeLedger).filter_by(
                        user_id=user_id
                    ).all()

                    if not entries:
                        return "No study progress recorded yet."

                    mastered = sum(1 for e in entries if e.status == "mastered")
                    learning = sum(1 for e in entries if e.status == "learning")
                    needs_review = sum(1 for e in entries if e.status == "needs_review")

                    return (
                        f"Overall Progress:\n"
                        f"- Mastered: {mastered} concepts\n"
                        f"- Learning: {learning} concepts\n"
                        f"- Needs Review: {needs_review} concepts\n"
                        f"- Total: {len(entries)} concepts"
                    )

        except Exception as e:
            logger.error(f"Error getting study progress: {e}")
            return f"Sorry, I couldn't retrieve your progress. Error: {str(e)}"


# Tool definitions for Azure AI Agent
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "set_reminder",
            "description": "Schedule a reminder for the user to study a specific topic at a specific time. Use this when the user asks to be reminded about something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user's unique identifier"
                    },
                    "task_name": {
                        "type": "string",
                        "description": "Name of the task or topic to remind about"
                    },
                    "reminder_time": {
                        "type": "string",
                        "description": "ISO format datetime string (e.g., '2026-03-26T16:00:00')"
                    },
                    "context": {
                        "type": "object",
                        "description": "Optional additional context about the reminder",
                        "additionalProperties": True
                    }
                },
                "required": ["user_id", "task_name", "reminder_time"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_webpage",
            "description": "Fetch and read the content of a webpage. Use this when the user provides a URL and wants you to read or analyze the content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to read"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_knowledge_ledger",
            "description": "Update the knowledge ledger with information about what the user has learned. Use this to track study progress and concepts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user's unique identifier"
                    },
                    "concept": {
                        "type": "string",
                        "description": "The concept being learned"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["learning", "mastered", "needs_review"],
                        "description": "Status of learning"
                    },
                    "confidence_score": {
                        "type": "integer",
                        "description": "User's confidence level (1-10)",
                        "minimum": 1,
                        "maximum": 10
                    },
                    "notes": {
                        "type": "string",
                        "description": "Optional notes about the concept"
                    }
                },
                "required": ["user_id", "concept"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_study_progress",
            "description": "Get the user's study progress for a specific concept or overall progress summary.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "The user's unique identifier"
                    },
                    "concept": {
                        "type": "string",
                        "description": "Optional specific concept to check progress for"
                    }
                },
                "required": ["user_id"]
            }
        }
    }
]
