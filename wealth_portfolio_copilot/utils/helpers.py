"""Utility functions for the Wealth & Portfolio Co-Pilot."""

import logging
import os
from datetime import datetime
from typing import Any, Dict


def setup_logging(log_level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Set up logging configuration.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        
    Returns:
        Configured logger
    """
    # Create logs directory if needed
    if log_file:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
    
    # Configure logging
    handlers = [logging.StreamHandler()]
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    
    return logging.getLogger("wealth_portfolio_copilot")


def format_currency(amount: float, currency: str = "USD") -> str:
    """
    Format a number as currency.
    
    Args:
        amount: Amount to format
        currency: Currency code
        
    Returns:
        Formatted currency string
    """
    symbols = {
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "JPY": "¥"
    }
    
    symbol = symbols.get(currency, currency)
    return f"{symbol}{amount:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a decimal as percentage.
    
    Args:
        value: Decimal value (e.g., 0.075 for 7.5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def parse_ticker(input_text: str) -> str:
    """
    Parse a stock ticker from user input.
    
    Args:
        input_text: User's input text
        
    Returns:
        Ticker symbol or None
    """
    import re
    
    # Look for uppercase letters (2-5 chars)
    tickers = re.findall(r'\b[A-Z]{2,5}\b', input_text)
    
    if tickers:
        return tickers[0]
    
    return None


def validate_portfolio_weights(weights: Dict[str, float]) -> bool:
    """
    Validate that portfolio weights sum to approximately 1.0.
    
    Args:
        weights: Dictionary of asset weights
        
    Returns:
        True if valid, False otherwise
    """
    total = sum(weights.values())
    return 0.99 <= total <= 1.01


def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        
    Returns:
        Truncated text with ellipsis if needed
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - 3] + "..."


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers, returning default if denominator is zero.
    
    Args:
        numerator: Numerator
        denominator: Denominator
        default: Default value if division by zero
        
    Returns:
        Result of division or default
    """
    if denominator == 0:
        return default
    
    return numerator / denominator
