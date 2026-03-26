# Study Companion Bot

A proactive, AI-powered study companion that acts like a friend - helping you learn, remembering everything you discuss, and checking in on your progress.

## Overview

The Study Companion Bot is designed for students (especially medical students) who want a learning partner that:

- **Remembers Everything**: Uses Mem0 for long-term memory and tracks all your learning progress
- **Proactive Check-ins**: Doesn't wait for you - initiates conversations at scheduled times
- **Deep Understanding**: Uses Socratic questioning to ensure you truly understand concepts
- **Web Reading**: Can read and analyze articles, papers, and web content you share
- **Smart Reminders**: Set custom reminders for study sessions
- **Progress Tracking**: Maintains a "knowledge ledger" of what you've learned

## Architecture

### Tech Stack

- **Azure OpenAI**: Powers the intelligent conversational AI
- **Mem0**: Long-term memory management (like a hippocampus)
- **PostgreSQL**: Persistent storage for users, reminders, and progress
- **Redis**: Caching and session management
- **n8n**: Automation platform for proactive check-ins and reminders
- **Telegram**: Primary messaging interface
- **FastAPI**: REST API for programmatic access
- **Docker**: Containerized deployment

### Components

1. **Azure AI Agent** (`src/agent.py`)
   - Conversational AI with tool-use capabilities
   - Integrates with Mem0 for context-aware responses
   - Generates proactive check-in messages

2. **Tools** (`src/tools.py`)
   - `set_reminder`: Schedule study reminders
   - `read_webpage`: Extract and analyze web content
   - `update_knowledge_ledger`: Track learning progress
   - `get_study_progress`: Retrieve progress reports

3. **Memory Manager** (`src/memory.py`)
   - Mem0 integration for long-term memory
   - Context retrieval for conversations
   - Fact extraction and storage

4. **Telegram Bot** (`src/telegram_bot.py`)
   - User-friendly chat interface
   - Command handlers (/start, /help, /progress)
   - Message routing to Azure AI agent

5. **REST API** (`src/api.py`)
   - Programmatic access to agent functionality
   - Proactive message generation endpoint
   - User and progress management

6. **n8n Workflows**
   - `reminder_workflow.json`: Automated reminder delivery
   - `web_scraper_workflow.json`: Web content extraction
   - `proactive_checkin_workflow.json`: Scheduled check-ins

## Setup

### Prerequisites

- Docker and Docker Compose
- Azure OpenAI API key and endpoint
- Telegram Bot Token (from @BotFather)
- (Optional) Mem0 API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd talkpal
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in:
   ```
   # Required
   AZURE_OPENAI_API_KEY=your_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   TELEGRAM_BOT_TOKEN=your_telegram_token

   # Optional
   MEM0_API_KEY=your_mem0_key
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   The database is automatically initialized on first startup.

5. **Import n8n workflows**
   - Access n8n at http://localhost:5678
   - Login with admin/changeme (change this!)
   - Import workflows from `n8n_workflows/` directory

### Configuration

#### Azure OpenAI Setup

1. Create an Azure OpenAI resource
2. Deploy a GPT-4 model
3. Copy the API key, endpoint, and deployment name to `.env`

#### Telegram Bot Setup

1. Message @BotFather on Telegram
2. Create a new bot with `/newbot`
3. Copy the bot token to `.env`
4. Start chatting with your bot!

#### n8n Workflows

1. **Reminder Workflow**
   - Receives reminder requests from the agent
   - Stores in database
   - Sends messages at scheduled times

2. **Web Scraper Workflow**
   - Extracts content from URLs
   - Cleans and formats text
   - Returns to agent

3. **Proactive Check-in Workflow**
   - Runs every 8 hours
   - Checks inactive users
   - Generates and sends check-in messages

## Usage

### Telegram Bot

Start a conversation with your bot on Telegram:

```
/start - Initialize the bot
/help - Get help
/progress - View your study progress
```

### Example Conversations

**Learning a concept:**
```
User: Can you help me understand Type 1 hypersensitivity?
Bot: Absolutely! Type 1 hypersensitivity is fascinating...
     [Explains concept]

     To check your understanding: What do you think happens
     when the allergen binds to IgE antibodies?
```

**Setting a reminder:**
```
User: Remind me to review this tomorrow at 4 PM
Bot: Got it! I've set a reminder for 'review this' at 2026-03-27 16:00.
     I'll make sure to check in with you then!
```

**Reading a webpage:**
```
User: Can you read this article and explain the key points?
     https://example.com/article
Bot: [Reads and analyzes the article]

     I've read through the article. Here are the key takeaways...
     How does this relate to what we discussed last week about...?
```

### REST API

The API is available at `http://localhost:8000`

**Chat endpoint:**
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "message": "Explain mitosis"
  }'
```

**Set reminder:**
```bash
curl -X POST http://localhost:8000/api/reminder \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "task_name": "Review cardiology notes",
    "reminder_time": "2026-03-27T16:00:00"
  }'
```

**Get progress:**
```bash
curl -X POST http://localhost:8000/api/progress \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123"
  }'
```

## Database Schema

### Users Table
- `id`: User identifier (Telegram chat ID)
- `username`: User's name
- `platform`: telegram/whatsapp
- `created_at`: Registration timestamp
- `last_active`: Last activity timestamp
- `preferences`: JSON preferences

### Reminders Table
- `id`: Auto-increment ID
- `user_id`: Foreign key to users
- `task_name`: Reminder description
- `reminder_time`: Scheduled time
- `status`: pending/sent/cancelled
- `context`: Additional context

### Knowledge Ledger Table
- `id`: Auto-increment ID
- `user_id`: Foreign key to users
- `concept`: Concept name
- `first_learned`: Initial learning timestamp
- `last_reviewed`: Last review timestamp
- `review_count`: Number of reviews
- `confidence_score`: 1-10 confidence level
- `status`: learning/mastered/needs_review

### Study Sessions Table
- `id`: Auto-increment ID
- `user_id`: Foreign key to users
- `topic`: Session topic
- `started_at`: Start timestamp
- `ended_at`: End timestamp
- `notes`: Session notes
- `concepts_covered`: JSON array
- `confidence_level`: 1-10

### Conversation Logs Table
- `id`: Auto-increment ID
- `user_id`: Foreign key to users
- `message`: Message content
- `role`: user/assistant/system
- `timestamp`: Message timestamp
- `metadata`: Additional metadata

## Deployment

### Docker Compose (Recommended)

The included `docker-compose.yml` provides a complete stack:

```bash
docker-compose up -d
```

Services:
- `postgres`: Database
- `redis`: Cache
- `app`: REST API
- `telegram-bot`: Telegram interface
- `n8n`: Automation platform

### Manual Deployment

For production deployment on platforms like Railway, Render, or AWS:

1. Deploy PostgreSQL database
2. Deploy Redis instance
3. Deploy the API service
4. Deploy the Telegram bot service
5. Deploy n8n (or use n8n.cloud)
6. Update environment variables

### Environment Variables

**Required:**
- `AZURE_OPENAI_API_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `DATABASE_URL`
- `TELEGRAM_BOT_TOKEN`
- `N8N_WEBHOOK_URL`

**Optional:**
- `MEM0_API_KEY`
- `REDIS_URL`
- `TWILIO_ACCOUNT_SID` (for WhatsApp)
- `TWILIO_AUTH_TOKEN`

## Monitoring and Logs

Logs are stored in the `logs/` directory:

```bash
# View API logs
docker-compose logs -f app

# View bot logs
docker-compose logs -f telegram-bot

# View all logs
docker-compose logs -f
```

## Troubleshooting

### Bot not responding
- Check Telegram bot token is correct
- Verify bot service is running: `docker-compose ps`
- Check logs: `docker-compose logs telegram-bot`

### Reminders not working
- Verify n8n is running: http://localhost:5678
- Check n8n workflows are imported and activated
- Verify webhook URL is correct in `.env`

### Database connection errors
- Check PostgreSQL is running: `docker-compose ps postgres`
- Verify DATABASE_URL in `.env`
- Check database logs: `docker-compose logs postgres`

## Development

### Running locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database
export DATABASE_URL=postgresql://user:pass@localhost:5432/studycompanion
python -c "from src.database import db; db.create_tables()"

# Run API
python src/api.py

# Run Telegram bot (in another terminal)
python src/telegram_bot.py
```

### Testing

```bash
# Test the agent
python -c "from src.agent import StudyCompanionAgent; agent = StudyCompanionAgent(); print(agent.chat('test_user', 'Hello!'))"

# Test tools
python -c "from src.tools import StudyCompanionTools; print(StudyCompanionTools.read_webpage('https://example.com'))"
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or feature requests, please open an issue on GitHub.

## Roadmap

Future enhancements:
- [ ] WhatsApp integration
- [ ] Voice message support
- [ ] Spaced repetition algorithm
- [ ] Study group features
- [ ] Mobile app
- [ ] Export study notes
- [ ] Integration with calendar apps
- [ ] Multi-language support
