"""
Search module for PyTorch Documentation Search Tool.
Combines embedding generation, database querying, and result formatting.
"""

from typing import List, Dict, Any, Optional
import re

from ptsearch.config import MAX_RESULTS, logger
from ptsearch.formatter import ResultFormatter
from ptsearch.database import DatabaseManager
from ptsearch.embedding import EmbeddingGenerator

class SearchEngine:
    """Main search engine that combines all components."""
    
    def __init__(self, database_manager: Optional[DatabaseManager] = None, 
                 embedding_generator: Optional[EmbeddingGenerator] = None):
        """Initialize search engine with components."""
        # Initialize components if not provided
        self.database = database_manager or DatabaseManager()
        self.embedder = embedding_generator or EmbeddingGenerator()
        self.formatter = ResultFormatter()
        
        logger.info("Search engine initialized")
    
    def search(self, query: str, num_results: int = MAX_RESULTS, 
               filter_type: Optional[str] = None) -> Dict[str, Any]:
        """Search for documents matching the query."""
        try:
            # Process query to get embedding and determine intent
            query_data = self._process_query(query)
            
            # Log search info
            logger.info(f"Searching for: '{query}' (code query: {query_data['is_code_query']})")
            
            # Create filters
            filters = {"chunk_type": filter_type} if filter_type else None
            
            # Query database
            raw_results = self.database.query(
                query_data["embedding"],
                n_results=num_results,
                filters=filters
            )
            
            # Format results
            formatted_results = self.formatter.format_results(raw_results, query)
            
            # Rank results based on query intent
            ranked_results = self.formatter.rank_results(
                formatted_results,
                query_data["is_code_query"]
            )
            
            return ranked_results
            
        except Exception as e:
            logger.error(f"Error during search: {e}")
            return {
                "error": str(e),
                "query": query,
                "results": []
            }
    
    def _process_query(self, query: str) -> Dict[str, Any]:
        """Process query to determine intent and generate embedding."""
        # Clean query
        query = query.strip()
        
        # Generate embedding
        embedding = self.embedder.generate_embedding(query)
        
        # Determine if this is a code query
        is_code_query = self._is_code_query(query)
        
        return {
            "query": query,
            "embedding": embedding,
            "is_code_query": is_code_query
        }
    
    def _is_code_query(self, query: str) -> bool:
        """Determine if a query is looking for code."""
        query_lower = query.lower()
        
        # Code indicator keywords
        code_indicators = [
            "code", "example", "implementation", "function", "class", "method",
            "snippet", "syntax", "parameter", "argument", "return", "import",
            "module", "api", "call", "invoke", "instantiate", "create", "initialize"
        ]
        
        # Check for code indicators
        for indicator in code_indicators:
            if indicator in query_lower:
                return True
        
        # Check for code patterns
        code_patterns = [
            "def ", "class ", "import ", "from ", "torch.", "nn.",
            "->", "=>", "==", "!=", "+=", "-=", "*=", "():", "@"
        ]
        
        for pattern in code_patterns:
            if pattern in query:
                return True
        
        return False