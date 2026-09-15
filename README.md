# Wealth & Portfolio Conversational Co-Pilot

A multi-turn financial assistant for retail banking or wealth management clients, deployed as a Telegram bot.

## Features

- **Context Engineering (Memory & State)**
  - Episodic Memory: Maintains current dialogue context
  - Semantic Memory: Stores user's risk tolerance, financial goals, and past advice
  
- **MCP & Tool Execution**
  - Market Data Server: Fetches live stock prices, SEC filings
  - Portfolio Math Server: Monte Carlo simulations, compound interest calculations
  
- **RAG & Governance**
  - Graph RAG for bank research and compliance guidelines
  - Responsible AI with LLM Guardrails (NeMo Guardrails)
  - Compliance disclaimers for financial advice
  
- **LLM/SLM Optimization**
  - Lightweight SLM for intent classification
  - Efficient routing to save tokens

## Project Structure

```
wealth_portfolio_copilot/
├── bot/
│   ├── __init__.py
│   └── telegram_bot.py          # Telegram bot handler
├── memory/
│   ├── __init__.py
│   ├── episodic_memory.py       # Short-term conversation context
│   └── semantic_memory.py       # Long-term user profile (vectorized)
├── mcp/
│   ├── __init__.py
│   ├── market_data_server.py    # Live stock prices, SEC filings
│   └── portfolio_math_server.py # Monte Carlo, compound interest
├── rag/
│   ├── __init__.py
│   ├── graph_rag.py             # Graph-based RAG for compliance
│   └── knowledge_base/          # Bank research documents
├── guardrails/
│   ├── __init__.py
│   └── nemoguardrails.py        # Compliance & safety guardrails
├── llm/
│   ├── __init__.py
│   └── intent_classifier.py     # SLM for intent classification
├── config/
│   ├── __init__.py
│   └── settings.py              # Configuration management
├── utils/
│   ├── __init__.py
│   └── helpers.py               # Utility functions
├── data/                        # Vector stores and databases
├── logs/                        # Application logs
├── main.py                      # Entry point
├── requirements.txt             # Dependencies
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore rules
└── README.md                    # This file
```

## Setup

1. **Clone and navigate to the project:**
```bash
cd wealth_portfolio_copilot
```

2. **Create a virtual environment (recommended):**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your values
```

5. **Get a Telegram Bot Token:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Copy the token and add it to your `.env` file as `TELEGRAM_BOT_TOKEN`

6. **Run the bot:**
```bash
python main.py
```

## Usage

Start a conversation with your Telegram bot to:
- Discuss market trends
- Get explanations of financial concepts
- Analyze your portfolio
- Simulate retirement "what-if" scenarios

## Compliance & Safety

This bot implements strict guardrails:
- Cannot provide definitive financial advice
- Mandatory compliance disclaimers
- Risk warnings for volatile investments

## License

MIT License
