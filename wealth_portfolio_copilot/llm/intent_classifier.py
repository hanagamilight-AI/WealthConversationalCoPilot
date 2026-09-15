"""Intent Classifier using lightweight SLM for efficient routing."""

from typing import Dict, Any, List, Optional
from enum import Enum
import re

from guardrails.nemoguardrails import IntentType


class IntentClassifier:
    """
    Lightweight intent classifier using rule-based approach.
    In production, this would use a quantized SLM like Llama-3-8B.
    
    Classifies user intents to route conversations efficiently and
    save expensive frontier-LLM tokens.
    """
    
    def __init__(self):
        """Initialize the intent classifier."""
        # Keyword patterns for each intent type
        self.intent_patterns = {
            IntentType.GREETING: [
                r'\b(hi|hello|hey|good morning|good afternoon|good evening)\b',
                r'\bhow are you\b',
                r'\bnice to meet you\b'
            ],
            IntentType.MARKET_DATA_REQUEST: [
                r'\b(stock price|stock quote|share price)\b',
                r'\b(ticker|symbol)\s+[A-Z]+\b',
                r'\b(AAPL|MSFT|GOOGL|AMZN|TSLA|NVDA|META|JPM|V|JNJ)\b',
                r'\b(market cap|pe ratio|dividend|earnings)\b',
                r'\b(show me.*stock|get.*price|look up.*ticker)\b'
            ],
            IntentType.PORTFOLIO_ANALYSIS: [
                r'\b(my portfolio|my investments|my holdings)\b',
                r'\b(portfolio allocation|asset allocation)\b',
                r'\b(diversification|rebalance)\b',
                r'\b(how am i doing|portfolio performance)\b',
                r'\b(analyze.*portfolio|review.*investments)\b'
            ],
            IntentType.RETIREMENT_PLANNING: [
                r'\b(retirement|retire)\b',
                r'\b(401k|IRA|Roth|pension)\b',
                r'\b(social security)\b',
                r'\b(when can i retire|retirement age)\b',
                r'\b(retirement savings|retirement income)\b',
                r'\b(monte carlo|what-if.*retirement)\b'
            ],
            IntentType.FINANCIAL_ADVICE: [
                r'\b(should i|should we)\b.*\b(invest|buy|sell|hold)\b',
                r'\b(what do you think|what\'s your opinion)\b',
                r'\b(recommend|recommendation|advise)\b',
                r'\b(is it good|is it safe|is it worth)\b',
                r'\b(best investment|best stock)\b'
            ],
            IntentType.HIGH_RISK_INVESTMENT: [
                r'\b(bitcoin|crypto|cryptocurrency)\b',
                r'\b(options|futures|derivatives)\b',
                r'\b(margin|leverage|short selling)\b',
                r'\b(penny stock|ipo)\b',
                r'\b(high risk|aggressive)\b'
            ],
            IntentType.COMPLIANCE_SENSITIVE: [
                r'\b(life savings|all my money|everything)\b',
                r'\b(borrow|loan|mortgage)\b.*\b(invest|stock)\b',
                r'\b(guarantee|risk-free|cannot lose)\b',
                r'\b(insider|tip)\b'
            ],
            IntentType.GENERAL_QUESTION: [
                r'\b(what is|explain|tell me about|how does)\b',
                r'\b(define|meaning|concept)\b',
                r'\b(difference between|compare)\b'
            ],
            IntentType.COMPLAINT: [
                r'\b(complaint|unhappy|dissatisfied)\b',
                r'\b(problem|issue|wrong)\b',
                r'\b(not working|doesn\'t work)\b',
                r'\b(angry|frustrated|disappointed)\b'
            ]
        }
        
        # Financial concept definitions for general questions
        self.concept_responses = {
            'pe ratio': "The P/E ratio (Price-to-Earnings) measures a company's current share price relative to its earnings per share.",
            'market cap': "Market capitalization is the total value of a company's outstanding shares, calculated as share price × total shares.",
            'dividend': "A dividend is a distribution of profits by a corporation to its shareholders.",
            'etf': "An ETF (Exchange-Traded Fund) is a type of investment fund that trades on stock exchanges.",
            'mutual fund': "A mutual fund pools money from many investors to invest in securities like stocks, bonds, and short-term debt.",
            'bond': "A bond is a fixed-income instrument representing a loan made by an investor to a borrower (typically corporate or governmental).",
            'roth ira': "A Roth IRA is a retirement account where contributions are made with after-tax dollars, allowing for tax-free growth.",
            '401k': "A 401(k) is an employer-sponsored retirement savings plan with tax advantages."
        }
    
    def classify(self, user_input: str) -> Dict[str, Any]:
        """
        Classify the user's intent.
        
        Args:
            user_input: User's message text
            
        Returns:
            Classification result with intent and confidence
        """
        user_input_lower = user_input.lower()
        
        intent_scores = {}
        
        # Score each intent type
        for intent_type, patterns in self.intent_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in patterns:
                if re.search(pattern, user_input_lower):
                    score += 1
                    matched_patterns.append(pattern)
            
            if score > 0:
                intent_scores[intent_type] = {
                    "score": score,
                    "matched_patterns": matched_patterns
                }
        
        # Determine primary intent
        if not intent_scores:
            return {
                "intent": IntentType.UNKNOWN,
                "confidence": 0.0,
                "all_scores": {},
                "suggested_response": None
            }
        
        # Get highest scoring intent
        primary_intent = max(intent_scores.keys(), key=lambda x: intent_scores[x]["score"])
        max_score = intent_scores[primary_intent]["score"]
        
        # Calculate confidence (normalized)
        total_score = sum(s["score"] for s in intent_scores.values())
        confidence = min(1.0, max_score / total_score) if total_score > 0 else 0.0
        
        # Generate suggested response for simple intents
        suggested_response = self._get_suggested_response(primary_intent, user_input_lower)
        
        return {
            "intent": primary_intent,
            "confidence": confidence,
            "all_scores": {k.value: v["score"] for k, v in intent_scores.items()},
            "matched_patterns": intent_scores[primary_intent]["matched_patterns"],
            "suggested_response": suggested_response,
            "requires_llm": self._requires_llm(primary_intent, confidence)
        }
    
    def _get_suggested_response(self, intent: IntentType, user_input: str) -> Optional[str]:
        """
        Get a pre-computed response for simple intents.
        
        Args:
            intent: Classified intent
            user_input: User's message
            
        Returns:
            Suggested response or None
        """
        if intent == IntentType.GREETING:
            return (
                "Hello! I'm your Wealth & Portfolio Co-Pilot. I can help you with:\n"
                "• Checking stock prices and market data\n"
                "• Analyzing your portfolio\n"
                "• Retirement planning and what-if scenarios\n"
                "• Explaining financial concepts\n\n"
                "How can I assist you today?"
            )
        
        elif intent == IntentType.GENERAL_QUESTION:
            # Check if it's a known concept
            for concept, definition in self.concept_responses.items():
                if concept in user_input:
                    return f"{definition}\n\n⚠️ This is for educational purposes only and not financial advice."
        
        return None
    
    def _requires_llm(self, intent: IntentType, confidence: float) -> bool:
        """
        Determine if the intent requires LLM processing.
        
        Args:
            intent: Classified intent
            confidence: Classification confidence
            
        Returns:
            True if LLM is required
        """
        # Simple intents can be handled without LLM
        non_llm_intents = [
            IntentType.GREETING,
        ]
        
        # High confidence simple intents don't need LLM
        if intent in non_llm_intents and confidence > 0.8:
            return False
        
        # Complex intents always need LLM
        llm_required_intents = [
            IntentType.FINANCIAL_ADVICE,
            IntentType.PORTFOLIO_ANALYSIS,
            IntentType.RETIREMENT_PLANNING,
        ]
        
        if intent in llm_required_intents:
            return True
        
        # Medium confidence might need LLM
        if confidence < 0.6:
            return True
        
        return False
    
    def batch_classify(self, inputs: List[str]) -> List[Dict[str, Any]]:
        """
        Classify multiple inputs.
        
        Args:
            inputs: List of user messages
            
        Returns:
            List of classification results
        """
        return [self.classify(input_text) for input_text in inputs]


# Singleton instance
intent_classifier = IntentClassifier()
