# Quick Start Guide

Get your Study Companion Bot up and running in 15 minutes!

## Prerequisites

- Docker Desktop installed
- Azure OpenAI API access
- Telegram account

## Step 1: Get API Credentials

### Azure OpenAI (Required)

1. Go to [Azure Portal](https://portal.azure.com)
2. Create or access an Azure OpenAI resource
3. Navigate to "Keys and Endpoint"
4. Copy:
   - API Key
   - Endpoint URL
   - Deployment name

### Telegram Bot (Required)

1. Open Telegram and search for `@BotFather`
2. Send `/newbot`
3. Follow instructions to create your bot
4. Copy the bot token (looks like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`)

### Mem0 (Optional)

1. Visit [Mem0.ai](https://mem0.ai)
2. Sign up for an account
3. Get your API key from the dashboard

## Step 2: Clone and Configure

```bash
# Clone the repository
git clone https://github.com/yourusername/talkpal.git
cd talkpal

# Copy environment template
cp .env.example .env
```

Edit `.env` with your credentials:

```bash
# Required - Azure OpenAI
AZURE_OPENAI_API_KEY=your_azure_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4

# Required - Telegram
TELEGRAM_BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# Optional - Mem0 (leave empty to use local storage)
MEM0_API_KEY=your_mem0_key_or_leave_empty

# These are auto-configured by docker-compose
DATABASE_URL=postgresql://studyuser:studypass@postgres:5432/studycompanion
REDIS_URL=redis://redis:6379
N8N_WEBHOOK_URL=http://n8n:5678/webhook
```

## Step 3: Launch Services

```bash
# Start all services
docker-compose up -d

# Check that everything is running
docker-compose ps
```

You should see 5 services running:
- `study-companion-db` (PostgreSQL)
- `study-companion-redis` (Redis)
- `study-companion-app` (API)
- `study-companion-telegram` (Bot)
- `study-companion-n8n` (Automation)

## Step 4: Configure n8n Workflows

1. Open your browser to http://localhost:5678
2. Login with:
   - Username: `admin`
   - Password: `changeme` (change this in production!)

3. Import workflows:
   - Click "Workflows" → "Import from File"
   - Import `n8n_workflows/reminder_workflow.json`
   - Click "Activate" (toggle in top-right)
   - Repeat for `web_scraper_workflow.json`
   - Repeat for `proactive_checkin_workflow.json`

4. Configure PostgreSQL credentials:
   - Click "Credentials" → "Add Credential"
   - Select "PostgreSQL"
   - Name: `Study Companion DB`
   - Host: `postgres`
   - Database: `studycompanion`
   - User: `studyuser`
   - Password: `studypass`
   - Save

5. Configure Telegram credentials:
   - Click "Credentials" → "Add Credential"
   - Select "Telegram"
   - Name: `Study Companion Bot`
   - Access Token: (your bot token)
   - Save

## Step 5: Test Your Bot

1. Open Telegram
2. Search for your bot (the username you created with @BotFather)
3. Send `/start`

You should receive a welcome message!

## Step 6: Try It Out

Test these features:

### Basic Chat
```
You: Hello! Can you help me study?
Bot: Hey! Absolutely, I'd love to help...
```

### Set a Reminder
```
You: Remind me to review this topic tomorrow at 2 PM
Bot: Got it! I've set a reminder...
```

### Read a Webpage
```
You: Can you read this article for me?
https://en.wikipedia.org/wiki/Mitosis
Bot: [Reads and summarizes the article]
```

### Check Progress
```
You: /progress
Bot: [Shows your study progress]
```

## Troubleshooting

### Bot doesn't respond

Check bot logs:
```bash
docker-compose logs -f telegram-bot
```

Common fixes:
- Verify `TELEGRAM_BOT_TOKEN` is correct
- Restart bot: `docker-compose restart telegram-bot`

### "Database connection error"

Check database:
```bash
docker-compose logs postgres
docker-compose restart postgres
```

### Reminders don't work

1. Check n8n is running: http://localhost:5678
2. Verify workflows are activated (green toggle)
3. Check workflow execution history in n8n

### "Azure OpenAI error"

Verify credentials:
```bash
# Check logs
docker-compose logs app

# Verify .env file
cat .env | grep AZURE_OPENAI
```

## Next Steps

### Customize the Bot

Edit the system prompt in `src/agent.py` to change personality:

```python
self.system_prompt = """You are a friendly study companion...
[Customize this text]
"""
```

### Add More Features

- Check `docs/ARCHITECTURE.md` for system design
- Explore `src/tools.py` to add new tools
- Create custom n8n workflows

### Deploy to Production

See `README.md` deployment section for:
- Railway.app deployment
- Render deployment
- AWS/GCP deployment

## Support

- Issues: https://github.com/yourusername/talkpal/issues
- Documentation: See `docs/` folder
- Email: your-email@example.com

## Success Checklist

- [x] Docker services running
- [x] n8n workflows imported and activated
- [x] Bot responds to `/start`
- [x] Can chat with bot
- [x] Reminders work
- [x] Web reading works
- [x] Progress tracking works

Congratulations! Your Study Companion Bot is ready! 🎉
