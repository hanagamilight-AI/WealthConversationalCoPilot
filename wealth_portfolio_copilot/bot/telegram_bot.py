"""Telegram Bot Handler for the Wealth & Portfolio Co-Pilot."""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from config.settings import settings
from memory import EpisodicMemory, SemanticMemory
from mcp import market_data_server, portfolio_math_server
from rag import knowledge_graph
from guardrails import compliance_checker, nemoguardrails, IntentType
from llm import intent_classifier

logger = logging.getLogger(__name__)


class WealthPortfolioBot:
    """
    Telegram bot handler for the Wealth & Portfolio Co-Pilot.
    Manages conversations, memory, and tool execution.
    """
    
    def __init__(self):
        """Initialize the bot."""
        self.app = None
        self.user_sessions: Dict[int, Dict[str, Any]] = {}
        self._initialize_knowledge_base()
    
    def _initialize_knowledge_base(self):
        """Initialize the knowledge base with sample data."""
        try:
            knowledge_graph.build_sample_knowledge_base()
            logger.info("Knowledge base initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize knowledge base: {e}")
    
    def _get_user_session(self, user_id: int) -> Dict[str, Any]:
        """
        Get or create a user session.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            User session dictionary
        """
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = {
                "episodic_memory": EpisodicMemory(max_turns=settings.MAX_EPISODIC_MEMORY),
                "semantic_memory": SemanticMemory(user_id=str(user_id)),
                "user_profile": None,
                "context": {}
            }
        return self.user_sessions[user_id]
    
    async def start_command(self, update: Update, context) -> None:
        """Handle /start command."""
        user_id = update.effective_user.id
        session = self._get_user_session(user_id)
        
        welcome_message = (
            f"👋 Welcome {update.effective_user.first_name}!\n\n"
            "I'm your **Wealth & Portfolio Co-Pilot**.\n\n"
            "I can help you with:\n"
            "• 📈 Checking stock prices and market data\n"
            "• 💼 Analyzing your portfolio\n"
            "• 🎯 Retirement planning and what-if scenarios\n"
            "• 📚 Explaining financial concepts\n\n"
            "⚠️ *Important*: I provide educational information only, not financial advice.\n\n"
            "How can I assist you today?"
        )
        
        # Store greeting in episodic memory
        session["episodic_memory"].add_message(
            role="assistant",
            content="Welcome message sent",
            metadata={"type": "greeting"}
        )
        
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    
    async def help_command(self, update: Update, context) -> None:
        """Handle /help command."""
        help_text = (
            "📖 **Available Commands**:\n\n"
            "/start - Start the conversation\n"
            "/portfolio - View your portfolio summary\n"
            "/retirement - Run retirement projections\n"
            "/stock <TICKER> - Get stock price (e.g., /stock AAPL)\n"
            "/profile - View your risk profile\n"
            "/reset - Reset conversation history\n\n"
            "💡 **Tips**:\n"
            "• Ask about specific stocks: 'What's the price of Tesla?'\n"
            "• Request analysis: 'Analyze my portfolio diversification'\n"
            "• Plan retirement: 'Run a Monte Carlo simulation for retirement'\n"
            "• Learn concepts: 'Explain P/E ratio'"
        )
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def stock_command(self, update: Update, context) -> None:
        """Handle /stock command."""
        if not context.args:
            await update.message.reply_text(
                "Please provide a stock ticker. Example: `/stock AAPL`",
                parse_mode='Markdown'
            )
            return
        
        ticker = context.args[0].upper()
        user_id = update.effective_user.id
        session = self._get_user_session(user_id)
        
        # Add to episodic memory
        session["episodic_memory"].add_message(
            role="user",
            content=f"Requesting stock price for {ticker}",
            metadata={"intent": "market_data_request", "ticker": ticker}
        )
        
        # Fetch stock data
        stock_data = await market_data_server.get_stock_price(ticker)
        
        if "error" in stock_data:
            response = f"❌ Error fetching data for {ticker}: {stock_data['error']}"
        else:
            response = (
                f"📈 **{ticker} Stock Price**\n\n"
                f"💰 Current Price: ${stock_data.get('current_price', 'N/A')}\n"
                f"📊 Market Cap: ${stock_data.get('market_cap', 'N/A'):,}\n"
                f"📉 P/E Ratio: {stock_data.get('pe_ratio', 'N/A')}\n"
                f"💵 Dividend Yield: {stock_data.get('dividend_yield', 'N/A')}\n"
                f"📅 52-Week Range: ${stock_data.get('52_week_low', 'N/A')} - ${stock_data.get('52_week_high', 'N/A')}\n\n"
                f"_Data as of {datetime.now().strftime('%Y-%m-%d %H:%M')}_\n\n"
                f"⚠️ This is not financial advice."
            )
        
        session["episodic_memory"].add_message(
            role="assistant",
            content=f"Stock data for {ticker}",
            metadata={"ticker": ticker}
        )
        
        await update.message.reply_text(response, parse_mode='Markdown')
    
    async def handle_message(self, update: Update, context) -> None:
        """Handle regular text messages."""
        user_id = update.effective_user.id
        user_input = update.message.text
        session = self._get_user_session(user_id)
        
        # Check compliance before processing
        compliance_result = compliance_checker.check_query(
            user_input,
            session.get("user_profile")
        )
        
        if not compliance_result["compliant"]:
            block_message = (
                "⚠️ **Compliance Notice**\n\n"
                "I cannot assist with this request as it may involve:\n"
                f"{chr(10).join(['• ' + b['message'] for b in compliance_result['blocks']])}\n\n"
                "Please consult with a qualified financial advisor for personalized advice."
            )
            await update.message.reply_text(block_message, parse_mode='Markdown')
            return
        
        # Classify intent
        classification = intent_classifier.classify(user_input)
        
        # Add to episodic memory
        session["episodic_memory"].add_message(
            role="user",
            content=user_input,
            metadata={"intent": classification["intent"].value}
        )
        
        # Handle simple intents without LLM
        if not classification["requires_llm"] and classification["suggested_response"]:
            await update.message.reply_text(classification["suggested_response"])
            return
        
        # Process based on intent
        response = await self._process_intent(
            user_input,
            classification,
            session
        )
        
        # Apply guardrails to response
        allowed, processed_response = await nemoguardrails.process_output(
            response,
            {
                "user_profile": session.get("user_profile"),
                "requires_disclaimer": compliance_result["requires_disclaimer"]
            }
        )
        
        # Add response to memory
        session["episodic_memory"].add_message(
            role="assistant",
            content=processed_response,
            metadata={"intent": classification["intent"].value}
        )
        
        await update.message.reply_text(processed_response, parse_mode='Markdown')
    
    async def _process_intent(
        self,
        user_input: str,
        classification: Dict[str, Any],
        session: Dict[str, Any]
    ) -> str:
        """
        Process user input based on classified intent.
        
        Args:
            user_input: User's message
            classification: Intent classification result
            session: User session
            
        Returns:
            Response text
        """
        intent = classification["intent"]
        
        if intent == IntentType.MARKET_DATA_REQUEST:
            # Extract ticker from input
            import re
            tickers = re.findall(r'\b[A-Z]{2,5}\b', user_input.upper())
            if tickers:
                ticker = tickers[0]
                stock_data = await market_data_server.get_stock_price(ticker)
                if "error" not in stock_data:
                    return (
                        f"📈 **{ticker}**\n"
                        f"Price: ${stock_data.get('current_price', 'N/A')}\n"
                        f"Market Cap: ${stock_data.get('market_cap', 'N/A'):,}"
                    )
            
            return "Could you please specify which stock ticker you'd like to check?"
        
        elif intent == IntentType.RETIREMENT_PLANNING:
            # Provide retirement planning info
            return (
                "🎯 **Retirement Planning**\n\n"
                "I can help you run Monte Carlo simulations for retirement planning.\n\n"
                "To get started, please share:\n"
                "• Current age\n"
                "• Desired retirement age\n"
                "• Current savings\n"
                "• Annual contributions\n\n"
                "Or use /retirement command for a quick projection."
            )
        
        elif intent == IntentType.HIGH_RISK_INVESTMENT:
            return (
                "⚠️ **High-Risk Investment Notice**\n\n"
                "You're asking about high-risk investments. These include:\n"
                "• Cryptocurrencies\n"
                "• Options and derivatives\n"
                "• Leveraged trading\n\n"
                "These investments carry significant risk of loss and may not be suitable for all investors.\n\n"
                "⚠️ **Risk Warning**: The investments discussed involve significant risk, including the potential loss of principal."
            )
        
        elif intent == IntentType.GENERAL_QUESTION:
            # Return the suggested response from classifier
            if classification["suggested_response"]:
                return classification["suggested_response"]
            
            return (
                "📚 I'd be happy to explain financial concepts. Could you be more specific about what you'd like to learn?\n\n"
                "Examples:\n"
                "• 'What is a P/E ratio?'\n"
                "• 'Explain ETFs'\n"
                "• 'What's the difference between Roth IRA and 401k?'"
            )
        
        else:
            # Default response for complex queries
            return (
                "Thank you for your question. Let me provide some insights...\n\n"
                "Based on our conversation, I understand you're interested in financial planning. "
                "Remember that all investments carry risk, and past performance doesn't guarantee future results.\n\n"
                "⚠️ This information is for educational purposes only and does not constitute financial advice."
            )
    
    async def reset_command(self, update: Update, context) -> None:
        """Handle /reset command."""
        user_id = update.effective_user.id
        if user_id in self.user_sessions:
            session = self.user_sessions[user_id]
            session["episodic_memory"].clear()
        
        await update.message.reply_text(
            "🔄 Conversation history has been reset. How can I help you today?"
        )
    
    def run(self):
        """Start the bot."""
        # Create application
        self.app = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()
        
        # Add handlers
        self.app.add_handler(CommandHandler("start", self.start_command))
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("stock", self.stock_command))
        self.app.add_handler(CommandHandler("reset", self.reset_command))
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        # Start the bot
        logger.info("Starting Wealth & Portfolio Co-Pilot bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)


def main():
    """Main entry point for the bot."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not set. Please set it in your environment or .env file.")
        print("\nTo get a bot token:")
        print("1. Open Telegram and search for @BotFather")
        print("2. Send /newbot command")
        print("3. Follow the instructions to create your bot")
        print("4. Copy the token and set TELEGRAM_BOT_TOKEN environment variable")
        return
    
    bot = WealthPortfolioBot()
    bot.run()


if __name__ == "__main__":
    main()
