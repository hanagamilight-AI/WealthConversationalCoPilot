"""Graph RAG for compliance and financial research."""

import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import networkx as nx
from langchain.vectorstores import Chroma
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from config.settings import settings


class FinancialKnowledgeGraph:
    """
    Graph-based RAG system for financial compliance and research.
    Maps relationships between companies, sectors, market trends, and compliance rules.
    """
    
    def __init__(self):
        """Initialize the knowledge graph."""
        self.graph = nx.DiGraph()
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL
        )
        
        # Vector store for document retrieval
        self.vector_store_path = os.path.join(
            settings.COMPLIANCE_DB_PATH if hasattr(settings, 'COMPLIANCE_DB_PATH') 
            else "./data/compliance_graph",
            "vector_store"
        )
        os.makedirs(self.vector_store_path, exist_ok=True)
        
        self.vector_store = Chroma(
            persist_directory=self.vector_store_path,
            embedding_function=self.embedding_model
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
    
    def add_entity(self, entity_id: str, entity_type: str, attributes: Dict[str, Any] = None) -> None:
        """
        Add an entity to the knowledge graph.
        
        Args:
            entity_id: Unique identifier for the entity
            entity_type: Type of entity (e.g., 'company', 'sector', 'regulation')
            attributes: Additional attributes
        """
        self.graph.add_node(
            entity_id,
            type=entity_type,
            attributes=attributes or {},
            created_at=datetime.now().isoformat()
        )
    
    def add_relationship(
        self,
        source: str,
        target: str,
        relationship_type: str,
        attributes: Dict[str, Any] = None
    ) -> None:
        """
        Add a relationship between two entities.
        
        Args:
            source: Source entity ID
            target: Target entity ID
            relationship_type: Type of relationship (e.g., 'operates_in', 'regulated_by')
            attributes: Additional attributes
        """
        self.graph.add_edge(
            source,
            target,
            type=relationship_type,
            attributes=attributes or {}
        )
    
    def add_compliance_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> None:
        """
        Add a compliance document to the knowledge base.
        
        Args:
            doc_id: Document identifier
            content: Document content
            metadata: Document metadata
        """
        # Split into chunks
        chunks = self.text_splitter.split_text(content)
        
        documents = []
        for i, chunk in enumerate(chunks):
            doc = Document(
                page_content=chunk,
                metadata={
                    **metadata,
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks)
                }
            )
            documents.append(doc)
        
        # Add to vector store
        self.vector_store.add_documents(documents)
        
        # Add to graph
        self.add_entity(doc_id, "document", metadata)
    
    def search_compliance(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search compliance documents.
        
        Args:
            query: Search query
            top_k: Number of results
            
        Returns:
            List of relevant documents
        """
        results = self.vector_store.similarity_search_with_score(query, k=top_k)
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "relevance_score": float(score)
            }
            for doc, score in results
        ]
    
    def find_related_entities(
        self,
        entity_id: str,
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Find entities related to a given entity.
        
        Args:
            entity_id: Starting entity ID
            relationship_types: Filter by relationship types
            max_depth: Maximum depth to traverse
            
        Returns:
            List of related entities with relationship info
        """
        related = []
        
        # BFS traversal
        visited = set()
        queue = [(entity_id, 0)]
        
        while queue:
            current, depth = queue.pop(0)
            
            if current in visited or depth > max_depth:
                continue
            
            visited.add(current)
            
            # Get neighbors
            for neighbor in self.graph.neighbors(current):
                edge_data = self.graph[current][neighbor]
                
                if relationship_types is None or edge_data['type'] in relationship_types:
                    neighbor_data = self.graph.nodes[neighbor]
                    related.append({
                        "entity_id": neighbor,
                        "entity_type": neighbor_data.get('type'),
                        "relationship_type": edge_data['type'],
                        "attributes": neighbor_data.get('attributes', {})
                    })
                    queue.append((neighbor, depth + 1))
        
        return related
    
    def get_sector_companies(self, sector: str) -> List[str]:
        """
        Get all companies in a sector.
        
        Args:
            sector: Sector name
            
        Returns:
            List of company IDs
        """
        companies = []
        
        for node, data in self.graph.nodes(data=True):
            if data.get('type') == 'company':
                # Check if company operates in this sector
                for neighbor in self.graph.predecessors(node):
                    neighbor_data = self.graph.nodes[neighbor]
                    if neighbor_data.get('type') == 'sector' and neighbor == sector:
                        companies.append(node)
        
        return companies
    
    def check_compliance_violation(
        self,
        action: str,
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Check if an action violates compliance rules.
        
        Args:
            action: The proposed action
            user_profile: User's risk profile and constraints
            
        Returns:
            Compliance check result
        """
        # Search for relevant compliance rules
        relevant_rules = self.search_compliance(action, top_k=3)
        
        violations = []
        warnings = []
        
        # Simple rule checking (in production, this would be more sophisticated)
        risk_tolerance = user_profile.get('risk_tolerance', 'moderate')
        
        # Example compliance checks
        if 'bitcoin' in action.lower() or 'crypto' in action.lower():
            if risk_tolerance == 'conservative':
                warnings.append(
                    "Cryptocurrency investments may not be suitable for conservative investors."
                )
        
        if 'life savings' in action.lower():
            warnings.append(
                "Investing life savings in a single asset violates diversification guidelines."
            )
        
        if 'margin' in action.lower() or 'leverage' in action.lower():
            if risk_tolerance in ['conservative', 'moderate']:
                warnings.append(
                    "Margin/leverage trading is not recommended for your risk profile."
                )
        
        return {
            "action": action,
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "relevant_rules": relevant_rules,
            "timestamp": datetime.now().isoformat()
        }
    
    def build_sample_knowledge_base(self) -> None:
        """Build a sample knowledge base for demonstration."""
        # Add sectors
        sectors = ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer Goods']
        for sector in sectors:
            self.add_entity(sector, 'sector')
        
        # Add sample companies
        companies = {
            'AAPL': ('Apple Inc.', 'Technology'),
            'MSFT': ('Microsoft Corporation', 'Technology'),
            'JNJ': ('Johnson & Johnson', 'Healthcare'),
            'JPM': ('JPMorgan Chase', 'Finance'),
            'XOM': ('Exxon Mobil', 'Energy')
        }
        
        for ticker, (name, sector) in companies.items():
            self.add_entity(ticker, 'company', {'name': name})
            self.add_relationship(ticker, sector, 'operates_in')
        
        # Add compliance rules
        compliance_docs = [
            {
                "doc_id": "COMP-001",
                "content": """
                Diversification Requirement: Clients should not invest more than 10% 
                of their portfolio in a single stock. Conservative clients should limit 
                to 5%. High-risk investments (cryptocurrency, derivatives) should not 
                exceed 5% of total portfolio for any client.
                """,
                "metadata": {"type": "compliance_rule", "category": "diversification"}
            },
            {
                "doc_id": "COMP-002",
                "content": """
                Risk Appropriateness: Investment recommendations must align with 
                client's stated risk tolerance. Conservative clients should only be 
                offered investment-grade bonds and blue-chip stocks. Moderate clients 
                can have up to 30% in growth stocks. Aggressive clients may have 
                exposure to emerging markets and alternative investments.
                """,
                "metadata": {"type": "compliance_rule", "category": "risk_appropriateness"}
            },
            {
                "doc_id": "COMP-003",
                "content": """
                Disclosure Requirements: All investment recommendations must include 
                clear disclosure that past performance does not guarantee future results. 
                Clients must be informed of all fees and potential conflicts of interest. 
                No guarantees of returns should be made.
                """,
                "metadata": {"type": "compliance_rule", "category": "disclosure"}
            }
        ]
        
        for doc in compliance_docs:
            self.add_compliance_document(
                doc["doc_id"],
                doc["content"],
                doc["metadata"]
            )


# Singleton instance
knowledge_graph = FinancialKnowledgeGraph()
