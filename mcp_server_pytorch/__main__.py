#!/usr/bin/env python3
"""
PyTorch Documentation Search Tool - MCP Server
Provides semantic search over PyTorch documentation with code-aware results.
"""

import sys
import argparse
import os

def main(argv=None):
    """Main entry point supporting both stdio and SSE transports."""
    parser = argparse.ArgumentParser(description="PyTorch Documentation Search MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                       help="Transport mechanism to use (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to for SSE transport")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to for SSE transport")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--max-results", type=int, default=5, help="Default maximum results to return")
    
    args = parser.parse_args(argv)
    
    # Initialize components
    from ptsearch.database import DatabaseManager
    from ptsearch.embedding import EmbeddingGenerator
    from ptsearch.search import SearchEngine
    
    # Initialize search components
    db_manager = DatabaseManager()
    embedding_generator = EmbeddingGenerator()
    search_engine = SearchEngine(db_manager, embedding_generator)
    
    # Run appropriate transport
    if args.transport == "stdio":
        from ptsearch.stdio import StdioMcpServer
        server = StdioMcpServer()
        server.start()
    else:
        from ptsearch.mcp import run_server
        run_server(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()