# Architecture Documentation

## System Overview

The Study Companion Bot is built as a microservices architecture with the following components:

```
┌─────────────────────────────────────────────────────────────┐
│                         User Interface                       │
│                    (Telegram / WhatsApp)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    Telegram Bot Service                      │
│                  (src/telegram_bot.py)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                  Azure AI Agent Core                         │
│                    (src/agent.py)                           │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Azure OpenAI │  │    Mem0      │  │    Tools     │     │
│  │   API        │  │   Memory     │  │   System     │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
┌───────▼────┐  ┌──────▼─────┐  ┌────▼────────┐
│ PostgreSQL │  │   Redis    │  │   n8n       │
│  Database  │  │   Cache    │  │ Workflows   │
└────────────┘  └────────────┘  └─────────────┘
```

## Core Components

### 1. Azure AI Agent

**File**: `src/agent.py`

The brain of the system. It:
- Processes user messages
- Maintains conversation context
- Decides when to use tools
- Generates responses with personality
- Creates proactive check-in messages

**Key Methods**:
- `chat()`: Process a user message and return response
- `generate_proactive_message()`: Create check-in messages
- `_execute_tool()`: Run tool functions
- `_log_conversation()`: Store conversation history

### 2. Memory Manager

**File**: `src/memory.py`

Handles long-term memory using Mem0:
- Stores facts about the user
- Retrieves relevant context
- Updates memories as user learns
- Links related concepts

**Key Methods**:
- `add_memory()`: Store new memory
- `search_memory()`: Find relevant memories
- `get_context_for_conversation()`: Get context for current chat

### 3. Tools System

**File**: `src/tools.py`

Implements agent capabilities:

#### set_reminder
- Schedules study reminders
- Stores in database
- Triggers n8n workflow

#### read_webpage
- Fetches web content
- Cleans and extracts text
- Returns formatted content

#### update_knowledge_ledger
- Tracks learning progress
- Updates confidence scores
- Maintains concept status

#### get_study_progress
- Retrieves progress reports
- Calculates statistics
- Formats for display

### 4. Database Layer

**File**: `src/models.py`, `src/database.py`

**Models**:
- **User**: User profiles and preferences
- **Reminder**: Scheduled reminders
- **KnowledgeLedger**: Learning progress tracking
- **StudySession**: Study session history
- **ConversationLog**: Full conversation history

**Database Manager**:
- SQLAlchemy ORM
- Connection pooling
- Transaction management

### 5. Telegram Bot

**File**: `src/telegram_bot.py`

User interface implementation:
- Command handlers
- Message routing
- Response formatting
- Typing indicators

**Commands**:
- `/start`: Initialize bot
- `/help`: Show help
- `/progress`: View progress

### 6. REST API

**File**: `src/api.py`

Programmatic access layer:
- Chat endpoint
- Reminder management
- Progress tracking
- User management

**Endpoints**:
- `POST /api/chat`: Send message
- `POST /api/proactive-message`: Generate check-in
- `POST /api/reminder`: Set reminder
- `POST /api/progress`: Get progress
- `GET /api/users`: List users

### 7. n8n Workflows

**Directory**: `n8n_workflows/`

Automation workflows:

#### Reminder Workflow
1. Webhook receives reminder request
2. Store in PostgreSQL
3. Schedule trigger checks every 5 minutes
4. Send reminders via Telegram when due
5. Update reminder status

#### Web Scraper Workflow
1. Webhook receives URL
2. HTTP request fetches page
3. Code node extracts text
4. Return cleaned content
5. Store in database

#### Proactive Check-in Workflow
1. Schedule trigger every 8 hours
2. Query inactive users
3. Generate personalized message
4. Send via Telegram

## Data Flow

### User Message Flow

```
User → Telegram → Bot Service → Agent Core
                                    ↓
                            Check Mem0 Memory
                                    ↓
                            Process with Azure OpenAI
                                    ↓
                            Execute Tools (if needed)
                                    ↓
                            Generate Response
                                    ↓
                            Update Memory
                                    ↓
                            Log Conversation
                                    ↓
User ← Telegram ← Bot Service ← Response
```

### Reminder Flow

```
User: "Remind me at 4 PM"
    ↓
Agent recognizes intent
    ↓
Calls set_reminder tool
    ↓
Stores in PostgreSQL
    ↓
Sends webhook to n8n
    ↓
n8n schedules reminder
    ↓
At 4 PM: n8n sends message
```

### Web Reading Flow

```
User: "Read this article: [URL]"
    ↓
Agent recognizes URL
    ↓
Calls read_webpage tool
    ↓
Sends to n8n scraper (or direct)
    ↓
n8n fetches and cleans content
    ↓
Returns to agent
    ↓
Agent analyzes content
    ↓
Responds with summary/insights
```

## Memory Architecture

### Short-term Memory
- Last 10-20 messages in conversation
- Stored in ConversationLog table
- Passed to Azure OpenAI

### Long-term Memory (Mem0)
- Important facts about user
- Learning preferences
- Concept relationships
- Retrieved on-demand

### Knowledge Ledger
- Structured learning progress
- Confidence scores
- Review history
- Mastery status

## Scalability Considerations

### Horizontal Scaling

**Bot Service**:
- Stateless design
- Multiple instances possible
- Load balanced

**API Service**:
- Stateless REST API
- Multiple instances
- Session in database

**Database**:
- PostgreSQL with read replicas
- Connection pooling
- Query optimization

**n8n**:
- Queue-based execution
- Can run multiple instances
- Shared database

### Performance Optimization

1. **Caching** (Redis):
   - User preferences
   - Recent conversations
   - Frequent queries

2. **Database Indexing**:
   - User lookups
   - Reminder queries
   - Conversation history

3. **Async Processing**:
   - Web scraping
   - Long-running operations
   - Background tasks

## Security

### API Keys
- Stored in environment variables
- Never committed to code
- Rotated regularly

### Database
- Encrypted connections
- Strong passwords
- Limited access

### User Data
- No sensitive medical information
- Encrypted at rest
- GDPR compliant

## Monitoring

### Logs
- Structured logging with Loguru
- Error tracking
- Performance metrics

### Health Checks
- Database connectivity
- Redis availability
- API responsiveness

### Metrics
- Message volume
- Response times
- Error rates
- User engagement

## Future Architecture

### Planned Enhancements

1. **Event Sourcing**:
   - Track all state changes
   - Replay capabilities
   - Audit trail

2. **Message Queue**:
   - Celery/RabbitMQ
   - Async processing
   - Job scheduling

3. **Microservices**:
   - Separate scraping service
   - Dedicated memory service
   - Analytics service

4. **API Gateway**:
   - Rate limiting
   - Authentication
   - Request routing
