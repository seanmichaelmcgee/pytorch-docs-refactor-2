#!/usr/bin/env python3
"""
STDIO transport handler for PyTorch Documentation Search Tool.
Provides MCP-compatible server using STDIO transport.
"""

import sys
import json
import logging
from typing import Dict, Any, Optional, List

from ptsearch.database import DatabaseManager
from ptsearch.embedding import EmbeddingGenerator
from ptsearch.search import SearchEngine
from ptsearch.config import OPENAI_API_KEY, logger
from ptsearch.mcp import TOOL_DESCRIPTOR

# Early API key validation
if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY not found. Please set this key before running the server.")
    print("Error: OPENAI_API_KEY not found in environment variables.", file=sys.stderr)
    print("Please set this key in your .env file or environment.", file=sys.stderr)
    sys.exit(1)

class StdioMcpServer:
    """MCP server implementation using stdio transport."""
    
    def __init__(self):
        """Initialize MCP server with search components."""
        # Initialize components
        self.db_manager = DatabaseManager()
        self.embedding_generator = EmbeddingGenerator()
        self.search_engine = SearchEngine(self.db_manager, self.embedding_generator)
        
        # Tool descriptor (using the same one from mcp.py)
        self.tool_descriptor = TOOL_DESCRIPTOR.copy()
        
        # Remove endpoint from tool descriptor as it's not needed for stdio
        if "endpoint" in self.tool_descriptor:
            del self.tool_descriptor["endpoint"]
    
    def start(self):
        """Start the server processing loop."""
        print("PyTorch Documentation Search STDIO Server started", file=sys.stderr)
        
        # Process messages in a loop
        try:
            while True:
                # Read a line from stdin
                line = sys.stdin.readline()
                if not line:
                    break
                
                # Process the line
                self._handle_message(line.strip())
        except KeyboardInterrupt:
            print("Server shutting down", file=sys.stderr)
    
    def _handle_message(self, message: str):
        """Handle a single MCP message."""
        try:
            # Parse the message
            data = json.loads(message)
            method = data.get("method", "")
            
            # Dispatch to the appropriate handler
            if method == "initialize":
                self._handle_initialize(data)
            elif method == "list_tools":
                self._handle_list_tools(data)
            elif method == "call_tool":
                self._handle_call_tool(data)
            else:
                self._send_error(data.get("id"), f"Unknown method: {method}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON: {message}")
            self._send_error(None, "Invalid JSON")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            self._send_error(None, f"Internal error: {str(e)}")
    
    def _handle_initialize(self, data: Dict[str, Any]):
        """Handle initialize request."""
        self._send_response(data.get("id"), {"capabilities": ["tools"]})
    
    def _handle_list_tools(self, data: Dict[str, Any]):
        """Handle list_tools request."""
        self._send_response(data.get("id"), {"tools": [self.tool_descriptor]})
    
    def _handle_call_tool(self, data: Dict[str, Any]):
        """Handle call_tool request."""
        params = data.get("params", {})
        tool_name = params.get("tool")
        args = params.get("args", {})
        
        if tool_name != self.tool_descriptor["name"]:
            self._send_error(data.get("id"), f"Unknown tool: {tool_name}")
            return
        
        # Extract search parameters
        query = args.get("query", "")
        n = int(args.get("num_results", 5))
        filter_type = args.get("filter", "")
        
        # Handle empty string filter as None
        if filter_type == "":
            filter_type = None
        
        # Execute search
        try:
            result = self.search_engine.search(query, n, filter_type)
            self._send_response(data.get("id"), {"result": result})
        except Exception as e:
            logger.error(f"Search error: {e}")
            self._send_error(data.get("id"), f"Search error: {str(e)}")
    
    def _send_response(self, id: Optional[str], result: Dict[str, Any]):
        """Send a successful response."""
        response = {
            "jsonrpc": "2.0",
            "id": id,
            "result": result
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    def _send_error(self, id: Optional[str], message: str, code: int = -32000):
        """Send an error response."""
        response = {
            "jsonrpc": "2.0",
            "id": id,
            "error": {
                "code": code,
                "message": message
            }
        }
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


def main():
    """Entry point for stdio server."""
    server = StdioMcpServer()
    server.start()


if __name__ == "__main__":
    main()