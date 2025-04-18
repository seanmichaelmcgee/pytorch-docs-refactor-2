"""
Embedding generation module for PyTorch Documentation Search Tool.
Handles generating embeddings with OpenAI API and basic caching.
"""

import os
import json
import hashlib
import time
from typing import List, Dict, Any, Optional

from openai import OpenAI

from ptsearch.config import (
    OPENAI_API_KEY, 
    EMBEDDING_MODEL, 
    EMBEDDING_DIMENSIONS,
    CACHE_DIR,
    MAX_CACHE_SIZE_GB,
    DEFAULT_CHUNKS_PATH,
    DEFAULT_EMBEDDINGS_PATH,
    logger
)

class EmbeddingGenerator:
    def __init__(self, api_key: str = OPENAI_API_KEY, model: str = EMBEDDING_MODEL, 
                 use_cache: bool = True, cache_dir: str = CACHE_DIR):
        """Initialize embedding generator with OpenAI API and basic caching."""
        self.model = model
        self.api_key = api_key
        self.use_cache = use_cache
        self.cache_dir = cache_dir
        self.stats = {"hits": 0, "misses": 0}
        
        # Validate API key early
        if not self.api_key:
            error_msg = "OPENAI_API_KEY not found. Please set this key in your .env file or environment."
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Initialize OpenAI client with compatibility handling
        self._initialize_client()
        
        # Initialize cache if enabled
        if use_cache:
            os.makedirs(cache_dir, exist_ok=True)
            logger.info(f"Embedding cache initialized at {cache_dir}")
    
    def _initialize_client(self):
        """Initialize OpenAI client with error handling for compatibility."""
        try:
            # Standard initialization
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except TypeError as e:
            # Handle proxies parameter error
            if "unexpected keyword argument 'proxies'" in str(e):
                import httpx
                logger.info("Creating custom HTTP client for OpenAI compatibility")
                http_client = httpx.Client(timeout=60.0)
                self.client = OpenAI(api_key=self.api_key, http_client=http_client)
            else:
                logger.error(f"Unexpected error initializing OpenAI client: {e}")
                raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text with caching."""
        if self.use_cache:
            # Check cache first
            cached_embedding = self._get_from_cache(text)
            if cached_embedding:
                self.stats["hits"] += 1
                return cached_embedding
        
        self.stats["misses"] += 1
        
        # Generate embedding via API
        try:
            response = self.client.embeddings.create(
                input=text,
                model=self.model
            )
            embedding = response.data[0].embedding
            
            # Cache the result
            if self.use_cache:
                self._save_to_cache(text, embedding)
            
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            # Return zeros as fallback
            return [0.0] * EMBEDDING_DIMENSIONS
    
    def generate_embeddings(self, texts: List[str], batch_size: int = 20) -> List[List[float]]:
        """Generate embeddings for multiple texts with batching."""
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = []
            
            # Check cache first
            uncached_texts = []
            uncached_indices = []
            
            if self.use_cache:
                for j, text in enumerate(batch_texts):
                    cached_embedding = self._get_from_cache(text)
                    if cached_embedding:
                        self.stats["hits"] += 1
                        batch_embeddings.append(cached_embedding)
                    else:
                        self.stats["misses"] += 1
                        uncached_texts.append(text)
                        uncached_indices.append(j)
            else:
                uncached_texts = batch_texts
                uncached_indices = list(range(len(batch_texts)))
                self.stats["misses"] += len(batch_texts)
            
            # Process uncached texts
            if uncached_texts:
                try:
                    response = self.client.embeddings.create(
                        input=uncached_texts,
                        model=self.model
                    )
                    
                    api_embeddings = [item.embedding for item in response.data]
                    
                    # Cache results
                    if self.use_cache:
                        for text, embedding in zip(uncached_texts, api_embeddings):
                            self._save_to_cache(text, embedding)
                    
                    # Place embeddings in correct order
                    for idx, embedding in zip(uncached_indices, api_embeddings):
                        while len(batch_embeddings) <= idx:
                            batch_embeddings.append(None)
                        batch_embeddings[idx] = embedding
                    
                except Exception as e:
                    logger.error(f"Error generating batch embeddings: {e}")
                    # Use zeros as fallback
                    for idx in uncached_indices:
                        while len(batch_embeddings) <= idx:
                            batch_embeddings.append(None)
                        batch_embeddings[idx] = [0.0] * EMBEDDING_DIMENSIONS
            
            # Ensure all positions have embeddings
            for j in range(len(batch_texts)):
                if j >= len(batch_embeddings) or batch_embeddings[j] is None:
                    batch_embeddings.append([0.0] * EMBEDDING_DIMENSIONS)
            
            all_embeddings.extend(batch_embeddings[:len(batch_texts)])
            
            # Respect API rate limits
            if i + batch_size < len(texts):
                time.sleep(0.5)
        
        return all_embeddings
    
    def embed_chunks(self, chunks: List[Dict[str, Any]], batch_size: int = 20) -> List[Dict[str, Any]]:
        """Generate embeddings for a list of chunks."""
        # Extract texts from chunks
        texts = [chunk["text"] for chunk in chunks]
        
        logger.info(f"Generating embeddings for {len(texts)} chunks using model {self.model}")
        print(f"Generating embeddings for {len(texts)} chunks using model {self.model}")
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts, batch_size)
        
        # Add embeddings to chunks
        for i, embedding in enumerate(embeddings):
            chunks[i]["embedding"] = embedding
        
        # Log cache stats
        if self.use_cache:
            hit_rate = self.stats["hits"] / (self.stats["hits"] + self.stats["misses"]) if (self.stats["hits"] + self.stats["misses"]) > 0 else 0
            logger.info(f"Cache hit rate: {hit_rate:.2%}")
            print(f"Cache hit rate: {hit_rate:.2%}")
        
        return chunks
    
    def process_file(self, input_file: str, output_file: Optional[str] = None) -> List[Dict[str, Any]]:
        """Process a file containing chunks and add embeddings."""
        logger.info(f"Loading chunks from {input_file}")
        print(f"Loading chunks from {input_file}")
        
        # Load chunks
        with open(input_file, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        logger.info(f"Loaded {len(chunks)} chunks")
        print(f"Loaded {len(chunks)} chunks")
        
        # Generate embeddings
        chunks_with_embeddings = self.embed_chunks(chunks)
        
        # Save to file if output_file is provided
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks_with_embeddings, f)
            logger.info(f"Saved {len(chunks_with_embeddings)} chunks with embeddings to {output_file}")
            print(f"Saved {len(chunks_with_embeddings)} chunks with embeddings to {output_file}")
        
        return chunks_with_embeddings
    
    def _get_cache_path(self, text: str) -> str:
        """Generate cache file path for a text."""
        text_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()
        return os.path.join(self.cache_dir, f"{text_hash}.json")
    
    def _get_from_cache(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache."""
        cache_path = self._get_cache_path(text)
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                return data.get("embedding")
            except Exception as e:
                logger.error(f"Error reading from cache: {e}")
        
        return None
    
    def _save_to_cache(self, text: str, embedding: List[float]) -> None:
        """Save embedding to cache."""
        cache_path = self._get_cache_path(text)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump({
                    "text_preview": text[:100] + "..." if len(text) > 100 else text,
                    "model": self.model,
                    "embedding": embedding,
                    "timestamp": time.time()
                }, f)
            
            # Manage cache size (simple LRU)
            self._manage_cache_size()
        except Exception as e:
            logger.error(f"Error writing to cache: {e}")
    
    def _manage_cache_size(self) -> None:
        """Manage cache size using LRU strategy."""
        max_size_bytes = int(MAX_CACHE_SIZE_GB * 1024 * 1024 * 1024)
        
        # Get all cache files with their info
        cache_files = []
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    stats = os.stat(filepath)
                    cache_files.append({
                        'path': filepath,
                        'size': stats.st_size,
                        'last_access': stats.st_atime
                    })
                except Exception:
                    pass
        
        # Calculate total size
        total_size = sum(f['size'] for f in cache_files)
        
        # If over limit, remove oldest files
        if total_size > max_size_bytes:
            # Sort by last access time (oldest first)
            cache_files.sort(key=lambda x: x['last_access'])
            
            # Remove files until under limit
            bytes_to_remove = total_size - max_size_bytes
            bytes_removed = 0
            removed_count = 0
            
            for file_info in cache_files:
                if bytes_removed >= bytes_to_remove:
                    break
                
                try:
                    os.remove(file_info['path'])
                    bytes_removed += file_info['size']
                    removed_count += 1
                except Exception:
                    pass
            
            logger.info(f"Removed {removed_count} cache files ({bytes_removed / 1024 / 1024:.2f} MB)")