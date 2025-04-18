"""
Configuration module for PyTorch Documentation Search Tool.
Centralizes all configuration settings and environment variables.
"""

import os
import logging
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ptsearch")

# Load environment variables
load_dotenv()

# API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY not found in environment variables")

# Model configuration
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072

# Document processing
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
OVERLAP_SIZE = int(os.getenv("OVERLAP_SIZE", "200"))

# Search configuration
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "5"))

# Database configuration
DB_DIR = os.getenv("DB_DIR", "./data/chroma_db")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "pytorch_docs")

# Cache configuration
CACHE_DIR = "./data/embedding_cache"
MAX_CACHE_SIZE_GB = 1.0

# File paths
DEFAULT_CHUNKS_PATH = "./data/chunks.json"
DEFAULT_EMBEDDINGS_PATH = "./data/chunks_with_embeddings.json"