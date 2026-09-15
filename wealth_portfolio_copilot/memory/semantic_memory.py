"""Semantic Memory - Long-term user profile storage using vector embeddings."""

import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import numpy as np

from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document

from config.settings import settings


@dataclass
class UserProfile:
    """Represents a user's long-term financial profile."""
    user_id: str
    risk_tolerance: str  # 'conservative', 'moderate', 'aggressive'
    financial_goals: List[str]
    investment_horizon: str  # 'short-term', 'medium-term', 'long-term'
    portfolio_value: Optional[float] = None
    asset_allocation: Optional[Dict[str, float]] = None
    past_advice: List[str] = None
    preferences: Dict[str, Any] = None
    created_at: datetime = None
    updated_at: datetime = None


class SemanticMemory:
    """
    Long-term memory storage using vector embeddings.
    Stores user profiles, financial goals, and historical advice.
    """
    
    def __init__(self, user_id: str = "default"):
        """
        Initialize semantic memory.
        
        Args:
            user_id: Unique identifier for the user
        """
        self.user_id = user_id
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
        
        # Initialize vector store
        self.vector_store_path = os.path.join(
            settings.VECTOR_DB_PATH, 
            f"user_{user_id}"
        )
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        self.vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embedding_model
        )
        
        self.user_profile: Optional[UserProfile] = None
    
    def create_or_update_profile(self, profile_data: Dict[str, Any]) -> UserProfile:
        """
        Create or update user profile.
        
        Args:
            profile_data: Dictionary containing profile information
            
        Returns:
            Updated UserProfile object
        """
        now = datetime.now()
        
        if self.user_profile:
            # Update existing profile
            for key, value in profile_data.items():
                if hasattr(self.user_profile, key):
                    setattr(self.user_profile, key, value)
            self.user_profile.updated_at = now
        else:
            # Create new profile
            self.user_profile = UserProfile(
                user_id=self.user_id,
                risk_tolerance=profile_data.get('risk_tolerance', 'moderate'),
                financial_goals=profile_data.get('financial_goals', []),
                investment_horizon=profile_data.get('investment_horizon', 'long-term'),
                portfolio_value=profile_data.get('portfolio_value'),
                asset_allocation=profile_data.get('asset_allocation'),
                past_advice=profile_data.get('past_advice', []),
                preferences=profile_data.get('preferences', {}),
                created_at=now,
                updated_at=now
            )
        
        # Store profile in vector database
        self._store_profile_in_vector_store()
        
        return self.user_profile
    
    def _store_profile_in_vector_store(self) -> None:
        """Store user profile information in vector database."""
        if not self.user_profile:
            return
        
        # Create documents from profile
        documents = []
        
        # Store financial goals
        for goal in self.user_profile.financial_goals:
            documents.append(Document(
                page_content=f"Financial Goal: {goal}",
                metadata={
                    "type": "goal",
                    "user_id": self.user_id,
                    "risk_tolerance": self.user_profile.risk_tolerance
                }
            ))
        
        # Store risk tolerance
        documents.append(Document(
            page_content=f"Risk Tolerance: {self.user_profile.risk_tolerance}. "
                        f"Investment Horizon: {self.user_profile.investment_horizon}",
            metadata={
                "type": "risk_profile",
                "user_id": self.user_id
            }
        ))
        
        # Store past advice
        for advice in self.user_profile.past_advice:
            documents.append(Document(
                page_content=f"Past Advice: {advice}",
                metadata={
                    "type": "advice",
                    "user_id": self.user_id,
                    "timestamp": self.user_profile.updated_at.isoformat()
                }
            ))
        
        # Add to vector store
        if documents:
            self.vector_store.add_documents(documents)
    
    def add_advice_to_memory(self, advice: str) -> None:
        """
        Add financial advice to long-term memory.
        
        Args:
            advice: The advice given to the user
        """
        if self.user_profile:
            self.user_profile.past_advice.append(advice)
            self.user_profile.updated_at = datetime.now()
            
            # Store in vector database
            doc = Document(
                page_content=f"Advice Given: {advice}",
                metadata={
                    "type": "advice",
                    "user_id": self.user_id,
                    "timestamp": self.user_profile.updated_at.isoformat()
                }
            )
            self.vector_store.add_documents([doc])
    
    def retrieve_relevant_context(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant information from long-term memory.
        
        Args:
            query: The query to search for
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with scores
        """
        if top_k is None:
            top_k = settings.SEMANTIC_MEMORY_TOP_K
        
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            }
            for doc, score in results
        ]
    
    def get_user_profile(self) -> Optional[UserProfile]:
        """Get the current user profile."""
        return self.user_profile
    
    def get_risk_profile_summary(self) -> str:
        """
        Get a summary of the user's risk profile.
        
        Returns:
            String summarizing risk tolerance and investment approach
        """
        if not self.user_profile:
            return "No risk profile available."
        
        return (
            f"Risk Tolerance: {self.user_profile.risk_tolerance}\n"
            f"Investment Horizon: {self.user_profile.investment_horizon}\n"
            f"Financial Goals: {', '.join(self.user_profile.financial_goals)}\n"
            f"Portfolio Value: ${self.user_profile.portfolio_value:,.2f}"
            if self.user_profile.portfolio_value
            else "Portfolio Value: Not specified"
        )
    
    def clear_memory(self) -> None:
        """Clear all stored memory for this user."""
        self.vector_store.delete_collection()
        self.user_profile = None
