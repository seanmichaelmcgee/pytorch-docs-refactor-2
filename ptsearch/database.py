"""
Database module for PyTorch Documentation Search Tool.
Handles storage and retrieval of chunks in ChromaDB.
"""

import os
import json
from typing import List, Dict, Any, Optional

import chromadb

from ptsearch.config import (
    DB_DIR, 
    COLLECTION_NAME, 
    EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDINGS_PATH,
    logger
)

class DatabaseManager:
    def __init__(self, db_dir: str = DB_DIR, collection_name: str = COLLECTION_NAME):
        """Initialize database manager for ChromaDB."""
        self.db_dir = db_dir
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        os.makedirs(db_dir, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=db_dir)
            logger.info(f"ChromaDB client initialized at {db_dir}")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}")
            raise
    
    def reset_collection(self) -> None:
        """Delete and recreate the collection with standard settings."""
        try:
            self.client.delete_collection(self.collection_name)
            logger.info(f"Deleted existing collection '{self.collection_name}'")
        except Exception as e:
            # Collection might not exist yet
            logger.info(f"No existing collection to delete: {e}")
        
        # Create a new collection with standard settings
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info(f"Created new collection '{self.collection_name}'")
        print(f"Created new collection '{self.collection_name}'")
    
    def get_collection(self):
        """Get or create the collection."""
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Retrieved existing collection '{self.collection_name}'")
        except Exception as e:
            # Collection doesn't exist, create it
            logger.info(f"Creating new collection: {e}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"Created new collection '{self.collection_name}'")
        
        return self.collection
    
    def add_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 50) -> None:
        """Add chunks to the collection with batching."""
        collection = self.get_collection()
        
        # Prepare data for ChromaDB
        ids = [chunk["id"] for chunk in chunks]
        embeddings = [self._ensure_vector_format(chunk["embedding"]) for chunk in chunks]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        # Add data in batches
        total_batches = (len(chunks) - 1) // batch_size + 1
        logger.info(f"Adding {len(chunks)} chunks in {total_batches} batches")
        print(f"Adding {len(chunks)} chunks in {total_batches} batches")
        
        for i in range(0, len(chunks), batch_size):
            end_idx = min(i + batch_size, len(chunks))
            batch_num = i // batch_size + 1
            
            try:
                collection.add(
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                logger.info(f"Added batch {batch_num}/{total_batches} ({end_idx - i} chunks)")
                print(f"Added batch {batch_num}/{total_batches} ({end_idx - i} chunks)")
            except Exception as e:
                logger.error(f"Error adding batch {batch_num}: {e}")
                print(f"Error adding batch {batch_num}: {e}")
    
    def query(self, query_embedding: List[float], n_results: int = 5, 
              filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Query the collection with vector search."""
        collection = self.get_collection()
        
        # Ensure query embedding has the correct format
        query_embedding = self._ensure_vector_format(query_embedding)
        
        # Prepare query parameters
        query_params = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"]
        }
        
        # Add filters if provided
        if filters:
            query_params["where"] = filters
        
        # Execute query
        try:
            results = collection.query(**query_params)
            
            # Format results for consistency
            formatted_results = {
                "ids": results.get("ids", [[]]),
                "documents": results.get("documents", [[]]),
                "metadatas": results.get("metadatas", [[]]),
                "distances": results.get("distances", [[]])
            }
            
            # Log query info
            if formatted_results["ids"] and formatted_results["ids"][0]:
                logger.info(f"Query returned {len(formatted_results['ids'][0])} results")
            
            return formatted_results
        except Exception as e:
            logger.error(f"Error during query: {e}")
            # Return empty results as fallback
            return {
                "ids": [[]],
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
    
    def load_from_file(self, filepath: str, reset: bool = True, batch_size: int = 50) -> None:
        """Load chunks from a file into ChromaDB."""
        logger.info(f"Loading chunks from {filepath}")
        print(f"Loading chunks from {filepath}")
        
        # Load the chunks
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            logger.info(f"Loaded {len(chunks)} chunks from file")
            print(f"Loaded {len(chunks)} chunks from file")
            
            # Reset collection if requested
            if reset:
                self.reset_collection()
            
            # Add chunks to collection
            self.add_chunks(chunks, batch_size)
            
            logger.info(f"Successfully loaded {len(chunks)} chunks into ChromaDB")
            print(f"Successfully loaded {len(chunks)} chunks into ChromaDB")
        except Exception as e:
            logger.error(f"Error loading from file: {e}")
            print(f"Error loading from file: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get basic statistics about the collection."""
        collection = self.get_collection()
        
        try:
            # Get count
            count = collection.count()
            
            return {
                "total_chunks": count,
                "collection_name": self.collection_name,
                "db_dir": self.db_dir
            }
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            return {
                "total_chunks": 0,
                "error": str(e)
            }
    
    def _ensure_vector_format(self, embedding: Any) -> List[float]:
        """Ensure vector is in the correct format for ChromaDB."""
        # Handle empty or None embeddings
        if not embedding:
            return [0.0] * EMBEDDING_DIMENSIONS
        
        # Handle NumPy arrays
        if hasattr(embedding, "tolist"):
            embedding = embedding.tolist()
        
        # Ensure all values are Python floats
        try:
            embedding = [float(x) for x in embedding]
        except Exception as e:
            logger.error(f"Error converting embedding values to float: {e}")
            return [0.0] * EMBEDDING_DIMENSIONS
        
        # Verify dimensions
        if len(embedding) != EMBEDDING_DIMENSIONS:
            # Pad or truncate if necessary
            if len(embedding) < EMBEDDING_DIMENSIONS:
                logger.warning(f"Padding embedding from {len(embedding)} to {EMBEDDING_DIMENSIONS} dimensions")
                embedding.extend([0.0] * (EMBEDDING_DIMENSIONS - len(embedding)))
            else:
                logger.warning(f"Truncating embedding from {len(embedding)} to {EMBEDDING_DIMENSIONS} dimensions")
                embedding = embedding[:EMBEDDING_DIMENSIONS]
        
        return embedding