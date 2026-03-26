"""
Telegram bot interface for the Study Companion
"""
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from loguru import logger
from config.settings import settings
from src.agent import StudyCompanionAgent
from src.database import db
from src.models import User


class TelegramBot:
    """Telegram bot handler"""

    def __init__(self):
        """Initialize the bot"""
        self.agent = StudyCompanionAgent()
        self.app = None

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)

        # Create or update user in database
        with db.get_session() as session:
            db_user = session.query(User).filter_by(id=chat_id).first()
            if not db_user:
                db_user = User(
                    id=chat_id,
                    username=user.username or user.first_name,
                    platform="telegram",
                    preferences={}
                )
                session.add(db_user)
                session.commit()

                welcome_msg = (
                    f"Hey {user.first_name}! 👋\n\n"
                    "I'm your Study Companion - think of me as your personal learning buddy! "
                    "I'm here to help you learn, remember what we discuss, and check in on your progress.\n\n"
                    "Here's what I can do:\n"
                    "• Discuss any topic and help you understand it deeply\n"
                    "• Remember everything we've talked about\n"
                    "• Read and analyze articles/papers you send me\n"
                    "• Set reminders for study sessions\n"
                    "• Track your learning progress\n"
                    "• Proactively check in to keep you on track\n\n"
                    "Just start chatting with me about anything you want to learn! "
                    "You can also send me links to read or ask me to remind you about topics.\n\n"
                    "Let's get started - what would you like to study today?"
                )
            else:
                db_user.last_active = datetime.utcnow()
                session.commit()

                welcome_msg = (
                    f"Welcome back, {user.first_name}! 😊\n\n"
                    "Ready to continue our learning journey? What would you like to work on today?"
                )

        await update.message.reply_text(welcome_msg)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = (
            "📚 *Study Companion Help*\n\n"
            "*Commands:*\n"
            "/start - Start or restart the bot\n"
            "/help - Show this help message\n"
            "/progress - View your study progress\n"
            "/remind - Set a reminder (or just ask me naturally)\n\n"
            "*How to use me:*\n"
            "• Just chat naturally about what you want to learn\n"
            "• Send me links to articles/papers to read and discuss\n"
            "• Ask me to explain concepts or test your understanding\n"
            "• Request reminders: 'Remind me to review this at 4 PM'\n"
            "• Check your progress: 'What have we learned so far?'\n\n"
            "I'm designed to be proactive - I'll check in on you and "
            "remind you to review concepts at the right time!"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")

    async def progress_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /progress command"""
        chat_id = str(update.effective_chat.id)

        # Get progress from agent
        progress = self.agent.tools.get_study_progress(chat_id)

        await update.message.reply_text(f"📊 *Your Study Progress*\n\n{progress}", parse_mode="Markdown")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular messages"""
        user = update.effective_user
        chat_id = str(update.effective_chat.id)
        message_text = update.message.text

        # Update last active time
        with db.get_session() as session:
            db_user = session.query(User).filter_by(id=chat_id).first()
            if db_user:
                db_user.last_active = datetime.utcnow()
                session.commit()

        # Show typing indicator
        await update.message.chat.send_action(action="typing")

        try:
            # Get conversation history from database
            from src.models import ConversationLog
            with db.get_session() as session:
                recent_logs = session.query(ConversationLog).filter_by(
                    user_id=chat_id
                ).order_by(ConversationLog.timestamp.desc()).limit(20).all()

                conversation_history = [
                    {"role": log.role, "content": log.message}
                    for log in reversed(recent_logs)
                ]

            # Get response from agent
            response = self.agent.chat(
                user_id=chat_id,
                message=message_text,
                conversation_history=conversation_history
            )

            # Send response
            await update.message.reply_text(response)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "I'm having trouble processing that right now. Could you try again?"
            )

    def run(self):
        """Run the bot"""
        if not settings.telegram_bot_token:
            logger.error("TELEGRAM_BOT_TOKEN not configured!")
            return

        logger.info("Starting Telegram bot...")

        # Create application
        self.app = Application.builder().token(settings.telegram_bot_token).build()

        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("progress", self.progress_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        # Run bot
        logger.info("Bot is running...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    # Initialize database
    db.create_tables()

    # Run bot
    bot = TelegramBot()
    bot.run()
