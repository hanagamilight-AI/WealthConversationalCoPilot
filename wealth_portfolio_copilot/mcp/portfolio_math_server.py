"""MCP Server for Portfolio Math - Monte Carlo simulations and financial calculations."""

import asyncio
from typing import Dict, Any, List, Optional
import numpy as np
from scipy.stats import norm
from datetime import datetime, timedelta


class PortfolioMathServer:
    """
    MCP Server for portfolio mathematics.
    Performs Monte Carlo simulations, compound interest calculations,
    and other financial computations without LLM hallucination.
    """
    
    def __init__(self):
        """Initialize the portfolio math server."""
        self.risk_free_rate = 0.05  # 5% annual risk-free rate
    
    async def calculate_compound_interest(
        self,
        principal: float,
        annual_rate: float,
        years: int,
        compounds_per_year: int = 12
    ) -> Dict[str, Any]:
        """
        Calculate compound interest.
        
        Args:
            principal: Initial investment amount
            annual_rate: Annual interest rate (as decimal, e.g., 0.07 for 7%)
            years: Number of years
            compounds_per_year: Number of times interest is compounded per year
            
        Returns:
            Dictionary with calculation results
        """
        try:
            # Compound interest formula: A = P(1 + r/n)^(nt)
            amount = principal * (1 + annual_rate / compounds_per_year) ** (compounds_per_year * years)
            total_interest = amount - principal
            
            # Year-by-year breakdown
            yearly_breakdown = []
            for year in range(1, years + 1):
                year_amount = principal * (1 + annual_rate / compounds_per_year) ** (compounds_per_year * year)
                yearly_breakdown.append({
                    "year": year,
                    "balance": round(year_amount, 2),
                    "interest_earned": round(year_amount - principal, 2)
                })
            
            return {
                "initial_principal": principal,
                "annual_rate": annual_rate,
                "years": years,
                "final_amount": round(amount, 2),
                "total_interest": round(total_interest, 2),
                "yearly_breakdown": yearly_breakdown,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_monte_carlo_simulation(
        self,
        initial_portfolio_value: float,
        annual_return_mean: float,
        annual_return_std: float,
        years: int,
        num_simulations: int = 10000,
        withdrawal_rate: float = 0.0
    ) -> Dict[str, Any]:
        """
        Run Monte Carlo simulation for retirement planning.
        
        Args:
            initial_portfolio_value: Starting portfolio value
            annual_return_mean: Expected annual return (as decimal)
            annual_return_std: Standard deviation of annual returns
            years: Number of years to simulate
            num_simulations: Number of simulation runs
            withdrawal_rate: Annual withdrawal rate (for retirement scenarios)
            
        Returns:
            Dictionary with simulation results
        """
        try:
            np.random.seed(42)  # For reproducibility
            
            # Generate random returns for each year and simulation
            random_returns = np.random.normal(
                annual_return_mean,
                annual_return_std,
                (num_simulations, years)
            )
            
            # Simulate portfolio growth
            portfolio_values = np.zeros((num_simulations, years + 1))
            portfolio_values[:, 0] = initial_portfolio_value
            
            for year in range(years):
                # Apply returns and withdrawals
                portfolio_values[:, year + 1] = (
                    portfolio_values[:, year] * (1 + random_returns[:, year]) -
                    portfolio_values[:, year] * withdrawal_rate
                )
            
            # Calculate statistics
            final_values = portfolio_values[:, -1]
            
            percentiles = {
                "10th": float(np.percentile(final_values, 10)),
                "25th": float(np.percentile(final_values, 25)),
                "50th": float(np.percentile(final_values, 50)),  # Median
                "75th": float(np.percentile(final_values, 75)),
                "90th": float(np.percentile(final_values, 90))
            }
            
            # Probability of success (not running out of money)
            success_count = np.sum(final_values > 0)
            success_rate = success_count / num_simulations
            
            # Worst and best cases
            worst_case = float(np.min(final_values))
            best_case = float(np.max(final_values))
            
            # Calculate probability distribution
            bins = 50
            histogram, bin_edges = np.histogram(final_values, bins=bins)
            
            return {
                "initial_portfolio_value": initial_portfolio_value,
                "annual_return_mean": annual_return_mean,
                "annual_return_std": annual_return_std,
                "years": years,
                "num_simulations": num_simulations,
                "withdrawal_rate": withdrawal_rate,
                "final_portfolio_statistics": {
                    "mean": float(np.mean(final_values)),
                    "median": percentiles["50th"],
                    "std_dev": float(np.std(final_values)),
                    "min": worst_case,
                    "max": best_case
                },
                "percentiles": percentiles,
                "success_rate": success_rate,
                "probability_of_ruin": 1 - success_rate,
                "histogram": {
                    "counts": histogram.tolist(),
                    "bin_edges": bin_edges.tolist()
                },
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def calculate_retirement_readiness(
        self,
        current_age: int,
        retirement_age: int,
        current_savings: float,
        annual_contribution: float,
        expected_return: float,
        desired_annual_income: float
    ) -> Dict[str, Any]:
        """
        Calculate retirement readiness.
        
        Args:
            current_age: Current age
            retirement_age: Desired retirement age
            current_savings: Current retirement savings
            annual_contribution: Annual contribution to retirement
            expected_return: Expected annual return
            desired_annual_income: Desired annual income in retirement
            
        Returns:
            Dictionary with retirement readiness analysis
        """
        try:
            years_to_retirement = retirement_age - current_age
            
            if years_to_retirement <= 0:
                return {
                    "error": "Retirement age must be greater than current age",
                    "timestamp": datetime.now().isoformat()
                }
            
            # Calculate future value of current savings
            fv_current = self._calculate_future_value(current_savings, expected_return, years_to_retirement)
            
            # Calculate future value of contributions
            fv_contributions = annual_contribution * ((1 + expected_return) ** years_to_retirement - 1) / expected_return
            
            # Total retirement savings at retirement
            total_at_retirement = fv_current + fv_contributions
            
            # Estimate years the money will last in retirement (4% rule)
            safe_withdrawal_rate = 0.04
            sustainable_annual_income = total_at_retirement * safe_withdrawal_rate
            
            years_money_lasts = total_at_retirement / desired_annual_income if desired_annual_income > 0 else float('inf')
            
            # Retirement readiness score (0-100)
            readiness_score = min(100, (sustainable_annual_income / desired_annual_income) * 100)
            
            return {
                "current_age": current_age,
                "retirement_age": retirement_age,
                "years_to_retirement": years_to_retirement,
                "current_savings": current_savings,
                "annual_contribution": annual_contribution,
                "expected_return": expected_return,
                "projected_savings_at_retirement": round(total_at_retirement, 2),
                "breakdown": {
                    "from_current_savings": round(fv_current, 2),
                    "from_contributions": round(fv_contributions, 2)
                },
                "sustainable_annual_income": round(sustainable_annual_income, 2),
                "desired_annual_income": desired_annual_income,
                "income_gap": round(desired_annual_income - sustainable_annual_income, 2),
                "years_money_will_last": round(years_money_lasts, 1),
                "retirement_readiness_score": round(readiness_score, 1),
                "recommendation": self._get_retirement_recommendation(readiness_score, years_money_lasts),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _calculate_future_value(self, present_value: float, rate: float, years: int) -> float:
        """Calculate future value of a lump sum."""
        return present_value * (1 + rate) ** years
    
    def _get_retirement_recommendation(self, readiness_score: float, years_money_lasts: float) -> str:
        """Generate retirement recommendation based on analysis."""
        if readiness_score >= 100:
            return "Excellent! You're on track to meet your retirement goals."
        elif readiness_score >= 80:
            return "Good progress. Consider increasing contributions slightly to ensure comfort."
        elif readiness_score >= 60:
            return "Moderate progress. You may need to adjust your retirement lifestyle or increase savings."
        elif readiness_score >= 40:
            return "Concerning. Significant changes needed: increase savings, delay retirement, or reduce expectations."
        else:
            return "Critical. Immediate action required. Consult a financial advisor."
    
    async def calculate_portfolio_metrics(
        self,
        portfolio_weights: Dict[str, float],
        asset_returns: Dict[str, float],
        asset_volatilities: Dict[str, float],
        correlation_matrix: Optional[Dict[str, Dict[str, float]]] = None
    ) -> Dict[str, Any]:
        """
        Calculate portfolio-level metrics.
        
        Args:
            portfolio_weights: Weights of each asset in the portfolio
            asset_returns: Expected annual returns for each asset
            asset_volatilities: Annual volatility (std dev) for each asset
            correlation_matrix: Correlation between assets
            
        Returns:
            Dictionary with portfolio metrics
        """
        try:
            assets = list(portfolio_weights.keys())
            n_assets = len(assets)
            
            # Convert to numpy arrays
            weights = np.array([portfolio_weights[asset] for asset in assets])
            returns = np.array([asset_returns[asset] for asset in assets])
            volatilities = np.array([asset_volatilities[asset] for asset in assets])
            
            # Expected portfolio return
            portfolio_return = np.sum(weights * returns)
            
            # Portfolio volatility (simplified - assumes zero correlation if not provided)
            if correlation_matrix:
                # Build covariance matrix from correlation
                cov_matrix = np.zeros((n_assets, n_assets))
                for i, asset_i in enumerate(assets):
                    for j, asset_j in enumerate(assets):
                        corr = correlation_matrix.get(asset_i, {}).get(asset_j, 0)
                        cov_matrix[i, j] = corr * volatilities[i] * volatilities[j]
            else:
                # Diagonal covariance matrix (no correlation)
                cov_matrix = np.diag(volatilities ** 2)
            
            # Portfolio variance and std dev
            portfolio_variance = np.dot(weights.T, np.dot(cov_matrix, weights))
            portfolio_volatility = np.sqrt(portfolio_variance)
            
            # Sharpe Ratio
            sharpe_ratio = (portfolio_return - self.risk_free_rate) / portfolio_volatility if portfolio_volatility > 0 else 0
            
            return {
                "assets": assets,
                "weights": {asset: float(portfolio_weights[asset]) for asset in assets},
                "expected_annual_return": float(portfolio_return),
                "annual_volatility": float(portfolio_volatility),
                "sharpe_ratio": float(sharpe_ratio),
                "risk_free_rate": self.risk_free_rate,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# Singleton instance
portfolio_math_server = PortfolioMathServer()
