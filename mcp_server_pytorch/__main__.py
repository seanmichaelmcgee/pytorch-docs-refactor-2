#!/usr/bin/env python3
"""
PyTorch Documentation Search Tool - MCP Server
Provides semantic search over PyTorch documentation with code-aware results.
"""

import sys
import argparse
import os
import signal
import time

from ptsearch.utils import logger
from ptsearch.utils.error import ConfigError
from ptsearch.config import settings
from ptsearch.core import DatabaseManager, EmbeddingGenerator, SearchEngine
from ptsearch.protocol import MCPProtocolHandler
from ptsearch.transport import STDIOTransport, SSETransport


def search_handler(args: dict) -> dict:
    """Handle search requests from the MCP protocol."""
    # Initialize components
    db_manager = DatabaseManager()
    embedding_generator = EmbeddingGenerator()
    search_engine = SearchEngine(db_manager, embedding_generator)
    
    # Extract search parameters
    query = args.get("query", "")
    n = int(args.get("num_results", settings.max_results))
    filter_type = args.get("filter", "")
    
    # Handle empty string filter as None
    if filter_type == "":
        filter_type = None
    
    # Execute search
    return search_engine.search(query, n, filter_type)


def setup_signal_handlers(transport):
    """Set up signal handlers for graceful shutdown."""
    def signal_handler(sig, frame):
        logger.info(f"Received signal {sig}, shutting down")
        transport.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def main(argv=None):
    """Main entry point for MCP server."""
    # Configure logging
    log_file = os.environ.get("MCP_LOG_FILE", "mcp_server.log")
    import logging
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(file_handler)
    
    parser = argparse.ArgumentParser(description="PyTorch Documentation Search MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                      help="Transport mechanism to use (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to for SSE transport")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to for SSE transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args(argv)
    
    # Log server startup
    logger.info("Starting PyTorch Documentation Search MCP Server",
               transport=args.transport,
               python_version=sys.version,
               current_dir=os.getcwd())
    
    # Validate settings
    errors = settings.validate()
    if errors:
        for key, error in errors.items():
            logger.error(f"Configuration error", field=key, error=error)
        raise ConfigError("Invalid configuration", details=errors)
    
    # Initialize protocol handler
    protocol_handler = MCPProtocolHandler(search_handler)
    
    try:
        # Initialize transport
        if args.transport == "stdio":
            transport = STDIOTransport(protocol_handler)
        else:
            transport = SSETransport(protocol_handler, args.host, args.port)
        
        # Setup signal handlers
        setup_signal_handlers(transport)
        
        # Start transport
        transport.start()
    except Exception as e:
        logger.exception(f"Fatal error", error=str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()