#!/usr/bin/env python3
"""
PyTorch Documentation Search Tool - MCP Server
Provides semantic search over PyTorch documentation with code-aware results.
"""

import sys
import argparse
import os
import logging

# Setup logging
log_file = os.environ.get("MCP_LOG_FILE", "mcp_server.log")
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("mcp_server")

def main(argv=None):
    """Main entry point supporting both stdio and SSE transports."""
    logger.debug("Server starting")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Current directory: {os.getcwd()}")
    
    parser = argparse.ArgumentParser(description="PyTorch Documentation Search MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                       help="Transport mechanism to use (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to for SSE transport")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to for SSE transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--max-results", type=int, default=5, help="Default maximum results to return")
    
    args = parser.parse_args(argv)
    
    # Verify environment variables
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY not set in environment")
        print("Error: OPENAI_API_KEY not found in environment variables.", file=sys.stderr)
        print("Please set this key in your .env file or environment.", file=sys.stderr)
        sys.exit(1)
    
    logger.debug(f"Using transport: {args.transport}")
    
    try:
        # Initialize components
        logger.debug("Importing required modules")
        from ptsearch.database import DatabaseManager
        from ptsearch.embedding import EmbeddingGenerator
        from ptsearch.search import SearchEngine
        
        logger.debug("Initializing search components")
        
        # Initialize search components
        db_manager = DatabaseManager()
        embedding_generator = EmbeddingGenerator()
        search_engine = SearchEngine(db_manager, embedding_generator)
        
        logger.debug("Search components initialized successfully")
        
        # Run appropriate transport
        if args.transport == "stdio":
            logger.debug("Starting STDIO transport")
            from ptsearch.stdio import StdioMcpServer
            server = StdioMcpServer()
            server.start()
        else:
            logger.debug(f"Starting SSE transport on {args.host}:{args.port}")
            from ptsearch.mcp import run_server
            run_server(host=args.host, port=args.port, debug=args.debug)
            
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        print(f"Error during startup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()