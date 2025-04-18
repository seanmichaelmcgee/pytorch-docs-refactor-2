#!/usr/bin/env python3
"""
Quick test script to verify the refactored search flow.
This script bypasses database and embedding calls with mocks.
"""

import json
from typing import Dict, Any, List

class MockDatabaseManager:
    """Mock database manager that returns pre-defined results."""
    
    def query(self, query_embedding: List[float], n_results: int = 5, 
              filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Return mock query results."""
        # Create mock results
        return {
            "ids": [["doc1", "doc2"]],
            "documents": [["This is a PyTorch DataLoader example.", "Another PyTorch sample."]],
            "metadatas": [[
                {"title": "DataLoader Example", "chunk_type": "code", "source": "https://pytorch.org/docs/stable/data.html"},
                {"title": "PyTorch Basics", "chunk_type": "text", "source": "https://pytorch.org/docs/stable/intro.html"}
            ]],
            "distances": [[0.1, 0.2]]
        }

class MockEmbeddingGenerator:
    """Mock embedding generator that returns a pre-defined embedding."""
    
    def generate_embedding(self, text: str) -> List[float]:
        """Return a mock embedding."""
        return [0.1] * 10  # Simple mock embedding

def main():
    """Run a test of the search flow with mocks."""
    print("Testing refactored search flow...")
    
    # Import the refactored components
    try:
        from ptsearch.core.search import SearchEngine
        from ptsearch.core.formatter import ResultFormatter
        
        # Create mock components
        db = MockDatabaseManager()
        embedder = MockEmbeddingGenerator()
        
        # Create search engine with mocks
        engine = SearchEngine(db, embedder)
        
        # Run a search
        query = "How to use DataLoader in PyTorch"
        results = engine.search(query)
        
        # Print results
        print(f"\nSearch Results for: '{query}'")
        print("-" * 40)
        print(json.dumps(results, indent=2))
        
        print("\n✅ Search flow test passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Search flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())