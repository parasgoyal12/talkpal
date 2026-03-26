"""
Azure AI Agent implementation for the Study Companion Bot
"""
import json
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI
from loguru import logger
from config.settings import settings
from src.tools import StudyCompanionTools, TOOL_DEFINITIONS
from src.memory import MemoryManager
from src.database import db
from src.models import ConversationLog


class StudyCompanionAgent:
    """
    Azure AI powered study companion agent with tools and memory.
    """

    def __init__(self):
        """Initialize the Azure AI agent"""
        self.client = AzureOpenAI(
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version,
            azure_endpoint=settings.azure_openai_endpoint
        )
        self.deployment_name = settings.azure_openai_deployment_name
        self.tools = StudyCompanionTools()
        self.memory_manager = MemoryManager(api_key=settings.mem0_api_key)

        # System prompt defining the agent's persona
        self.system_prompt = """You are a friendly, proactive study companion - like a peer mentor or senior resident.

Your role is to:
1. Help users learn and understand concepts deeply through Socratic questioning
2. Remember everything you've discussed and build on previous conversations
3. Track what the user has learned, what they struggle with, and their progress
4. Proactively check in on concepts that need review
5. Be conversational and supportive, not formal or robotic

Your personality:
- Use casual, friendly language like talking to a study buddy
- Show excitement when the user grasps concepts
- Acknowledge when topics are difficult
- Ask follow-up questions to ensure true understanding
- Reference previous conversations naturally

When the user discusses a topic:
- Use update_knowledge_ledger to track what they're learning
- Store important facts about their preferences and learning style in memory
- Ask probing questions to check understanding, don't just give answers

When the user shares a link:
- Use read_webpage to extract and analyze the content
- Discuss the key points and how they relate to what you've already studied

When the user asks to be reminded:
- Use set_reminder to schedule check-ins at specific times
- Include context about why the reminder was set

Remember: You're not a search engine or textbook. You're a friend who's on this learning journey together."""

    def _log_conversation(self, user_id: str, message: str, role: str, metadata: Optional[Dict] = None):
        """Log conversation to database"""
        try:
            with db.get_session() as session:
                log_entry = ConversationLog(
                    user_id=user_id,
                    message=message,
                    role=role,
                    metadata=metadata or {}
                )
                session.add(log_entry)
                session.commit()
        except Exception as e:
            logger.error(f"Error logging conversation: {e}")

    def _execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Execute a tool and return the result"""
        try:
            if tool_name == "set_reminder":
                return self.tools.set_reminder(**arguments)
            elif tool_name == "read_webpage":
                return self.tools.read_webpage(**arguments)
            elif tool_name == "update_knowledge_ledger":
                return self.tools.update_knowledge_ledger(**arguments)
            elif tool_name == "get_study_progress":
                return self.tools.get_study_progress(**arguments)
            else:
                return f"Unknown tool: {tool_name}"
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return f"Error executing {tool_name}: {str(e)}"

    def chat(
        self,
        user_id: str,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Process a chat message from the user.

        Args:
            user_id: User identifier
            message: User's message
            conversation_history: Optional conversation history

        Returns:
            Agent's response
        """
        try:
            # Log user message
            self._log_conversation(user_id, message, "user")

            # Get context from Mem0
            memory_context = self.memory_manager.get_context_for_conversation(user_id, message)

            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]

            # Add memory context if available
            if memory_context:
                messages.append({
                    "role": "system",
                    "content": memory_context
                })

            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history[-10:])  # Last 10 messages

            # Add current message
            messages.append({"role": "user", "content": message})

            # Call Azure OpenAI with tools
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000
            )

            response_message = response.choices[0].message

            # Handle tool calls
            if response_message.tool_calls:
                # Execute tools
                tool_messages = []

                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_arguments = json.loads(tool_call.function.arguments)

                    logger.info(f"Executing tool: {tool_name} with args: {tool_arguments}")

                    # Inject user_id if needed
                    if "user_id" in tool_arguments and not tool_arguments["user_id"]:
                        tool_arguments["user_id"] = user_id

                    tool_result = self._execute_tool(tool_name, tool_arguments)

                    tool_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })

                # Add tool responses and get final response
                messages.append(response_message)
                messages.extend(tool_messages)

                final_response = self.client.chat.completions.create(
                    model=self.deployment_name,
                    messages=messages,
                    temperature=0.7,
                    max_tokens=1000
                )

                assistant_message = final_response.choices[0].message.content
            else:
                assistant_message = response_message.content

            # Log assistant message
            self._log_conversation(user_id, assistant_message, "assistant")

            # Store important information in Mem0
            if any(keyword in message.lower() for keyword in ["struggle", "difficult", "confused", "don't understand"]):
                self.memory_manager.add_memory(
                    f"User struggled with: {message}",
                    user_id,
                    metadata={"type": "difficulty"}
                )
            elif any(keyword in message.lower() for keyword in ["understand", "get it", "makes sense", "clear"]):
                self.memory_manager.add_memory(
                    f"User understood: {message}",
                    user_id,
                    metadata={"type": "mastery"}
                )

            return assistant_message

        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return "I'm having trouble processing that right now. Could you try rephrasing?"

    def generate_proactive_message(self, user_id: str, context: Optional[Dict] = None) -> str:
        """
        Generate a proactive check-in message based on user's history.

        Args:
            user_id: User identifier
            context: Optional context for the check-in

        Returns:
            Proactive message
        """
        try:
            # Get recent memories
            memories = self.memory_manager.get_all_memories(user_id)

            # Get concepts that need review
            from src.models import KnowledgeLedger
            from datetime import datetime, timedelta

            with db.get_session() as session:
                # Find concepts not reviewed in last 24 hours
                yesterday = datetime.utcnow() - timedelta(days=1)
                concepts_to_review = session.query(KnowledgeLedger).filter(
                    KnowledgeLedger.user_id == user_id,
                    KnowledgeLedger.last_reviewed < yesterday,
                    KnowledgeLedger.status != "mastered"
                ).limit(3).all()

                review_context = ""
                if concepts_to_review:
                    concepts_list = [c.concept for c in concepts_to_review]
                    review_context = f"Concepts that need review: {', '.join(concepts_list)}"

            # Build prompt for proactive message
            prompt = f"""Based on the user's learning history, generate a friendly, proactive check-in message.

Context:
{review_context}

Recent activity: {len(memories)} topics discussed

Generate a brief, friendly message that:
1. Checks in on their progress
2. Suggests reviewing specific concepts if needed
3. Asks if they're ready to study or need a break
4. Sounds like a supportive friend, not a reminder app

Keep it conversational and brief (2-3 sentences)."""

            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": prompt}
            ]

            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=0.8,
                max_tokens=150
            )

            message = response.choices[0].message.content
            self._log_conversation(user_id, message, "assistant", {"type": "proactive"})

            return message

        except Exception as e:
            logger.error(f"Error generating proactive message: {e}")
            return "Hey! Just checking in - how's your studying going today?"
