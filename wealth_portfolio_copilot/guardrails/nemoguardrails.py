"""LLM Guardrails for compliance and safety."""

import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from enum import Enum

from config.settings import settings


class IntentType(Enum):
    """Types of user intents."""
    GREETING = "greeting"
    MARKET_DATA_REQUEST = "market_data_request"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"
    RETIREMENT_PLANNING = "retirement_planning"
    FINANCIAL_ADVICE = "financial_advice"
    HIGH_RISK_INVESTMENT = "high_risk_investment"
    COMPLIANCE_SENSITIVE = "compliance_sensitive"
    GENERAL_QUESTION = "general_question"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"


class ComplianceChecker:
    """
    Checks user queries and LLM responses for compliance issues.
    Implements hard-coded guardrails for financial advice.
    """
    
    # Patterns that trigger compliance warnings
    HIGH_RISK_PATTERNS = [
        r'\blife savings\b',
        r'\ball in\b',
        r'\bborrow.*invest\b',
        r'\bmortgage.*stock\b',
        r'\bput.*everything\b',
        r'\bsell.*house\b',
    ]
    
    HIGH_RISK_ASSETS = [
        'bitcoin', 'crypto', 'cryptocurrency',
        'options', 'futures', 'derivatives',
        'margin', 'leverage', 'short selling',
        'penny stock', 'ipo', 'spam stock'
    ]
    
    ADVICE_PATTERNS = [
        r'\bshould i\b',
        r'\bwhat should\b',
        r'\bis it a good idea\b',
        r'\bwould you recommend\b',
        r'\badvise me\b',
        r'\btell me to\b'
    ]
    
    def __init__(self):
        """Initialize the compliance checker."""
        self.enabled = settings.ENABLE_GUARDRAILS
    
    def check_query(self, query: str, user_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check a user query for compliance issues.
        
        Args:
            query: User's query text
            user_profile: User's risk profile
            
        Returns:
            Compliance check result
        """
        if not self.enabled:
            return {"compliant": True, "warnings": [], "blocks": []}
        
        warnings = []
        blocks = []
        requires_disclaimer = False
        
        query_lower = query.lower()
        
        # Check for high-risk patterns
        for pattern in self.HIGH_RISK_PATTERNS:
            if re.search(pattern, query_lower):
                blocks.append({
                    "type": "high_risk_behavior",
                    "pattern": pattern,
                    "message": "This query suggests potentially risky financial behavior."
                })
        
        # Check for high-risk assets
        for asset in self.HIGH_RISK_ASSETS:
            if asset in query_lower:
                warnings.append({
                    "type": "high_risk_asset",
                    "asset": asset,
                    "message": f"Discussion of {asset} requires risk disclosure."
                })
                requires_disclaimer = True
        
        # Check for financial advice requests
        for pattern in self.ADVICE_PATTERNS:
            if re.search(pattern, query_lower):
                requires_disclaimer = True
                warnings.append({
                    "type": "financial_advice_request",
                    "message": "Query requests financial advice. Disclaimer required."
                })
        
        # Check user profile compatibility
        if user_profile:
            risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
            
            if risk_tolerance == 'conservative':
                for asset in ['crypto', 'options', 'emerging markets', 'small cap']:
                    if asset in query_lower:
                        blocks.append({
                            "type": "risk_mismatch",
                            "message": f"{asset} is not suitable for conservative investors."
                        })
        
        return {
            "query": query,
            "compliant": len(blocks) == 0,
            "warnings": warnings,
            "blocks": blocks,
            "requires_disclaimer": requires_disclaimer,
            "timestamp": datetime.now().isoformat()
        }
    
    def check_response(self, response: str) -> Dict[str, Any]:
        """
        Check an LLM response for compliance issues.
        
        Args:
            response: LLM's response text
            
        Returns:
            Compliance check result
        """
        if not self.enabled:
            return {"compliant": True, "issues": []}
        
        issues = []
        response_lower = response.lower()
        
        # Check for prohibited statements
        prohibited_patterns = [
            (r'\bguarantee\b', "Cannot guarantee returns"),
            (r'\brisk-free\b', "Cannot claim investments are risk-free"),
            (r'\bwill make money\b', "Cannot promise profits"),
            (r'\bcannot lose\b', "Cannot claim no possibility of loss"),
            (r'\bbest investment\b', "Cannot claim something is the best"),
            (r'\byou must\b', "Cannot use imperative language for advice"),
        ]
        
        for pattern, reason in prohibited_patterns:
            if re.search(pattern, response_lower):
                issues.append({
                    "type": "prohibited_statement",
                    "pattern": pattern,
                    "reason": reason
                })
        
        # Check for missing disclaimer when needed
        if any(word in response_lower for word in ['invest', 'buy', 'sell', 'stock']):
            if 'not financial advice' not in response_lower and 'consult' not in response_lower:
                issues.append({
                    "type": "missing_disclaimer",
                    "reason": "Financial discussion without proper disclaimer"
                })
        
        return {
            "response": response,
            "compliant": len(issues) == 0,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_required_disclaimer(self, context: str = "general") -> str:
        """
        Get the appropriate disclaimer for a given context.
        
        Args:
            context: The context type
            
        Returns:
            Disclaimer text
        """
        disclaimers = {
            "general": """
⚠️ **Important Disclosure**: This information is for educational purposes only and 
does not constitute financial advice. Past performance does not guarantee future results. 
Please consult with a qualified financial advisor before making investment decisions.
""",
            "high_risk": """
⚠️ **Risk Warning**: The investments discussed involve significant risk, including 
the potential loss of principal. These may not be suitable for all investors. 
Please carefully consider your risk tolerance and consult with a financial advisor.
""",
            "retirement": """
⚠️ **Retirement Planning Notice**: Retirement projections are estimates based on 
assumptions that may not materialize. Actual results will vary. Please consult with 
a retirement planning specialist for personalized advice.
"""
        }
        
        return disclaimers.get(context, disclaimers["general"])


class NeMoGuardrailsIntegration:
    """
    Integration with NVIDIA NeMo Guardrails.
    Provides additional layer of safety and compliance.
    """
    
    def __init__(self):
        """Initialize NeMo Guardrails integration."""
        self.enabled = settings.ENABLE_GUARDRAILS
        # In production, this would initialize actual NeMo Guardrails
        self.rails_config = self._load_rails_config()
    
    def _load_rails_config(self) -> Dict[str, Any]:
        """Load guardrails configuration."""
        return {
            "models": [
                {
                    "engine": "openai",
                    "model": settings.OPENAI_MODEL
                }
            ],
            "rails": {
                "input": {
                    "flows": [
                        "check financial advice request",
                        "detect high risk queries",
                        "validate user intent"
                    ]
                },
                "output": {
                    "flows": [
                        "ensure disclaimer present",
                        "check for guarantees",
                        "validate compliance"
                    ]
                },
                "retrieval": {
                    "flows": [
                        "fetch compliance rules",
                        "get relevant regulations"
                    ]
                }
            },
            "custom_actions": [
                "add_financial_disclaimer",
                "block_prohibited_advice",
                "route_to_compliance_review"
            ]
        }
    
    async def process_input(self, user_input: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process user input through guardrails.
        
        Args:
            user_input: User's message
            context: Conversation context
            
        Returns:
            Tuple of (allowed, modified_input or block_reason)
        """
        if not self.enabled:
            return True, user_input
        
        # Simplified implementation
        # In production, this would use actual NeMo Guardrails
        
        compliance_checker = ComplianceChecker()
        result = compliance_checker.check_query(user_input, context.get('user_profile'))
        
        if not result["compliant"]:
            return False, f"Blocked: {result['blocks'][0]['message']}"
        
        return True, user_input
    
    async def process_output(self, llm_response: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Process LLM output through guardrails.
        
        Args:
            llm_response: LLM's response
            context: Conversation context
            
        Returns:
            Tuple of (allowed, modified_response or block_reason)
        """
        if not self.enabled:
            return True, llm_response
        
        compliance_checker = ComplianceChecker()
        result = compliance_checker.check_response(llm_response)
        
        if not result["compliant"]:
            # Add disclaimer if missing
            if any(issue["type"] == "missing_disclaimer" for issue in result["issues"]):
                disclaimer = compliance_checker.get_required_disclaimer("general")
                return True, llm_response + "\n\n" + disclaimer
            
            return False, f"Blocked: {result['issues'][0]['reason']}"
        
        # Add disclaimer if required by context
        if context.get('requires_disclaimer'):
            disclaimer = compliance_checker.get_required_disclaimer(
                context.get('disclaimer_type', 'general')
            )
            return True, llm_response + "\n\n" + disclaimer
        
        return True, llm_response


# Singleton instances
compliance_checker = ComplianceChecker()
nemoguardrails = NeMoGuardrailsIntegration()
