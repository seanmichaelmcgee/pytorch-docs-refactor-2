# PyTorch Documentation Search Tool MCP Integration Analysis

After reviewing your codebase and the reference documentation, I've identified several issues that may be causing the connection failures with your PyTorch Documentation Search MCP server. I'll outline the problems and provide specific solutions to get your server working correctly with UVX.

## Key Issues Identified

1. **Schema Version Issue**: Your tool descriptor is missing the required schema version
2. **UVX Configuration Complexity**: Your UVX configuration is more complex than necessary
3. **Environment Variable Handling**: OpenAI API key may not be passed correctly
4. **Process Termination**: The server may be exiting early due to initialization failures
5. **JSON Schema Format**: The enum handling in your input schema may be problematic

## Recommended Fixes

### 1. Fix the Tool Descriptor Format

The tool descriptor in both `ptsearch/mcp.py` and `ptsearch/stdio.py` needs the `schema_version` field:

```python
TOOL_DESCRIPTOR = {
    "name": TOOL_NAME,
    "schema_version": "1.0",  # Add this line
    "type": "function",
    # Rest of your descriptor...
}
```

Also, fix the enum in the input schema to ensure it only contains string values:

```python
"filter": {"type": "string", "enum": ["code", "text", ""]}
```

### 2. Simplify UVX Configuration

Your `.uvx/tool.json` is using a complex bash command chain. Looking at the successful "fetch" server, we should simplify:

```json
{
  "name": "mcp-server-pytorch",
  "version": "0.1.0",
  "description": "PyTorch Documentation Search Tool with MCP integration",
  "entrypoint": {
    "stdio": {
      "command": "python",
      "args": ["-m", "mcp_server_pytorch"]
    }
  },
  "requires": [
    "openai",
    "flask",
    "chromadb",
    "tree-sitter",
    "tree-sitter-languages",
    "python-dotenv",
    "tqdm",
    "numpy",
    "flask-cors"
  ]
}
```

This matches the successful "fetch" server's pattern more closely.

### 3. Enhance MCP Server Entry Point

Modify `mcp_server_pytorch/__main__.py` to include better error handling and logging:

```python
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

def main():
    """Main entry point supporting both stdio and SSE transports."""
    logger.debug("Server starting")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Current directory: {os.getcwd()}")
    
    parser = argparse.ArgumentParser(description="PyTorch Documentation Search MCP Server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio",
                       help="Transport mechanism to use (default: stdio)")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to for SSE transport")
    parser.add_argument("--port", type=int, default=5000, help="Port to bind to for SSE transport")
    
    args = parser.parse_args()
    
    # Verify environment variables
    if "OPENAI_API_KEY" not in os.environ:
        logger.error("OPENAI_API_KEY not set in environment")
        print("Error: OPENAI_API_KEY not found in environment variables.", file=sys.stderr)
        print("Please set this key in your .env file or environment.", file=sys.stderr)
        sys.exit(1)
    
    logger.debug(f"Using transport: {args.transport}")
    
    try:
        # Initialize components
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
            run_server(host=args.host, port=args.port)
            
    except Exception as e:
        logger.error(f"Error during startup: {e}", exc_info=True)
        print(f"Error during startup: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### 4. Create a Test Script

To verify your MCP implementation works independently of Claude, create this test script:

```python
#!/usr/bin/env python3
"""
Test script for PyTorch Documentation Search MCP Server.
Sends basic MCP protocol messages and verifies responses.
"""

import sys
import json
import subprocess
import time
import os

def send_message(proc, message):
    """Send a message to the process."""
    print(f"Sending: {message}", file=sys.stderr)
    proc.stdin.write(json.dumps(message) + "\n")
    proc.stdin.flush()

def read_message(proc):
    """Read a message from the process."""
    line = proc.stdout.readline().strip()
    print(f"Received: {line}", file=sys.stderr)
    if not line:
        return None
    return json.loads(line)

def main():
    """Run MCP protocol test."""
    # Start the MCP server
    proc = subprocess.Popen(
        ["python", "-m", "mcp_server_pytorch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={"OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY"), "PATH": os.environ.get("PATH", "")}
    )

    try:
        # Send initialize request
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": "1",
            "method": "initialize"
        })
        
        # Read initialize response
        init_response = read_message(proc)
        if not init_response or "result" not in init_response:
            print("Initialize failed", file=sys.stderr)
            return 1
        
        # Send list_tools request
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": "2",
            "method": "list_tools"
        })
        
        # Read list_tools response
        list_response = read_message(proc)
        if not list_response or "result" not in list_response:
            print("List tools failed", file=sys.stderr)
            return 1
        
        # Verify tool is present
        tools = list_response["result"].get("tools", [])
        if not tools:
            print("No tools found", file=sys.stderr)
            return 1
        
        print(f"Found tools: {tools}", file=sys.stderr)
        
        # Success
        print("MCP protocol test passed!", file=sys.stderr)
        return 0
        
    finally:
        # Clean up
        proc.terminate()
        proc.wait(timeout=5)

if __name__ == "__main__":
    sys.exit(main())
```

### 5. Use Minimal Environment Dependencies

For faster startup in the UVX context, use your `minimal_env.yml` to ensure only necessary dependencies are included.

### 6. Explicit Environment Variable Passing

When registering with Claude CLI, explicitly pass the OpenAI API key:

```bash
# Ensure OpenAI API key is set
export OPENAI_API_KEY=your_key_here

# Register the MCP server with explicit env passing
claude mcp add pytorch_search uvx mcp-server-pytorch -e OPENAI_API_KEY=${OPENAI_API_KEY}
```

## Implementation Steps

Follow these steps to get your MCP server working:

1. **Update Tool Descriptor**:
   - Add schema version to `ptsearch/mcp.py` and `ptsearch/stdio.py`
   - Fix the enum values in the input schema

2. **Simplify UVX Configuration**:
   - Update `.uvx/tool.json` to match the simplified pattern
   - Focus on the minimal, direct execution approach

3. **Enhance Entry Point**:
   - Update `mcp_server_pytorch/__main__.py` with robust error handling
   - Add detailed logging for troubleshooting

4. **Create Test Script**:
   - Implement and run the test script to verify MCP protocol works
   - Debug any issues before connecting to Claude

5. **Update Installation Docs**:
   - Update documentation with correct installation steps
   - Include troubleshooting guidance

6. **Register with Claude CLI**:
   - Register the server with explicit environment variable passing
   - Verify registration with `claude mcp list`

## Testing Protocol

To validate your implementation:

1. Run the test script to verify the MCP protocol works
2. Monitor the logs for any initialization issues
3. Register with Claude CLI and verify registration
4. Try a simple query from Claude to test end-to-end functionality

## Summary

The main issues appear to be related to schema versioning, UVX configuration complexity, and potential environment variable handling. By simplifying your approach to match the successful "fetch" server pattern, adding robust error handling, and ensuring proper environment variable passing, you should be able to get your PyTorch Documentation Search tool working with Claude Code.