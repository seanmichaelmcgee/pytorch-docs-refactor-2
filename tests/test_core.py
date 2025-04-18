#!/usr/bin/env python3
"""
Basic tests for PyTorch Documentation Search Tool core modules.
"""

import sys
import os
import unittest
import tempfile
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ptsearch.document import DocumentProcessor
from ptsearch.embedding import EmbeddingGenerator
from ptsearch.database import DatabaseManager
from ptsearch.search import SearchEngine

class CoreModulesTest(unittest.TestCase):
    def test_document_processor(self):
        """Test that the document processor properly chunks content."""
        processor = DocumentProcessor(chunk_size=100, overlap=20)
        
        # Create a temporary markdown file
        with tempfile.NamedTemporaryFile(suffix='.md', mode='w+', delete=False) as f:
            f.write("# Test Document\n\nThis is a test paragraph.\n\n")
            f.write("```python\ndef hello_world():\n    print('Hello, world!')\n```\n\n")
            f.write("Another paragraph.\n")
            filepath = f.name
        
        try:
            # Process the file
            chunks = processor.process_file(filepath)
            
            # Check results
            self.assertTrue(len(chunks) > 0)
            self.assertEqual(chunks[0]['metadata']['source'], os.path.basename(filepath))
            
            # Verify we have both code and text chunks
            chunk_types = [chunk['metadata']['chunk_type'] for chunk in chunks]
            self.assertIn('code', chunk_types)
            self.assertIn('text', chunk_types)
            
        finally:
            # Clean up
            os.unlink(filepath)
    
    def test_embedding_generator(self):
        """Test that the embedding generator can generate embeddings."""
        generator = EmbeddingGenerator(use_cache=True)
        
        # Test generating a single embedding
        text = "Test embedding generation"
        embedding = generator.generate_embedding(text)
        
        # Verify embedding shape
        self.assertEqual(len(embedding), 3072)  # Assuming text-embedding-3-large
    
    def test_simple_search_flow(self):
        """Test the basic search flow with mock components."""
        # This is a basic integration test that mocks the API calls
        
        class MockEmbeddingGenerator:
            def generate_embedding(self, text):
                # Return a fixed embedding for any text
                return [0.1] * 3072
        
        class MockDatabaseManager:
            def query(self, embedding, n_results=5, filters=None):
                # Return mock results
                return {
                    "ids": [["1", "2"]],
                    "documents": [["Test document", "Another document"]],
                    "metadatas": [[
                        {"title": "Test", "source": "test.md", "chunk_type": "text"},
                        {"title": "Example", "source": "example.py", "chunk_type": "code"}
                    ]],
                    "distances": [[0.1, 0.2]]
                }
        
        # Create search engine with mock components
        search_engine = SearchEngine(MockDatabaseManager(), MockEmbeddingGenerator())
        
        # Test search
        results = search_engine.search("test query")
        
        # Verify results
        self.assertIn("results", results)
        self.assertEqual(len(results["results"]), 2)
        self.assertEqual(results["query"], "test query")
        self.assertIn("count", results)

if __name__ == '__main__':
    unittest.main()