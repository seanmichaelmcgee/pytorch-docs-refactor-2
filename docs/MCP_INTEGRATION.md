# PyTorch Documentation Search - MCP Integration Guide

This guide explains how to integrate the refactored PyTorch Documentation Search Tool with Claude using the Model Context Protocol (MCP).

## Overview

The Model Context Protocol is Anthropic's standard for tool integration with Claude. Our refactored codebase includes a simplified MCP-compatible server that makes integration straightforward.

## Server Implementation

The `ptsearch/mcp.py` module implements an MCP-compatible server with the following key components:

1. **Tool Descriptor**: Defines the tool's capabilities, parameters, and endpoint
2. **SSE Endpoint**: Provides tool discovery via server-sent events
3. **Call Handler**: Processes tool invocations and returns search results

## Setup Instructions

### 1. Activate the Conda Environment

```bash
# Activate the environment
conda activate pytorch_docs_search
```

### 2. Start the MCP Server

```bash
# Navigate to the project root
cd /path/to/pytorch-docs-search

# Run the MCP server 
python -m ptsearch.mcp

# Or use the CLI
ptsearch server
```

You should see the following output:
```
Starting PyTorch Documentation Search Server on 0.0.0.0:5000
Run: claude mcp add --transport sse pytorch_search http://localhost:5000/events
 * Serving Flask app 'mcp'
 * Debug mode: off
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
```

### 3. Register the Tool with Claude Code CLI

In a new terminal window, run:

```bash
claude mcp add --transport sse pytorch_search http://localhost:5000/events
```

### 4. Verify Registration

Check that the tool is registered correctly:

```bash
claude mcp list
```

You should see `search_pytorch_docs` in the list of available tools.

## Usage

### Testing with CLI

To test the tool directly from the command line:

```bash
claude run tool search_pytorch_docs --input '{"query": "freeze layers in PyTorch"}'
```

For filtering results:

```bash
claude run tool search_pytorch_docs --input '{"query": "batch normalization", "filter": "code"}'
```

To retrieve more results:

```bash
claude run tool search_pytorch_docs --input '{"query": "autograd example", "num_results": 10}'
```

### Using with Claude CLI

When using Claude CLI, you can integrate the tool into your conversations:

```bash
claude run
```

Then within your conversation with Claude, you can ask about PyTorch topics and Claude will automatically use the tool to search the documentation.

### Direct API Testing

You can also test the search API directly:

```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "tensor operations", "num_results": 3}'
```

## Monitoring and Troubleshooting

All API requests are logged with detailed information. Common issues you might encounter:

### Common Issues

1. **Tool Registration Fails**
   - Ensure the server is running
   - Check that you have the correct URL (http://localhost:5000/events)
   - Verify you have the latest Claude CLI installed

2. **Server Won't Start**
   - Verify the port 5000 is available
   - Ensure all dependencies are installed in your environment
   - Check for any import errors in the console output

3. **No Results Returned**
   - Verify that the ChromaDB database has been populated
   - Check that the OpenAI API key is set correctly in .env
   - Look for error messages in the server logs

4. **"Unknown tool" Error**
   - Ensure you're using the correct tool name: `search_pytorch_docs`
   - Check the registration with `claude mcp list`

## Architecture

The MCP server implementation in `mcp.py` follows a simple flow:

1. **Tool Discovery**: `/events` endpoint for SSE-based tool registration
2. **Call Handling**: `/tools/call` endpoint processes tool invocations
3. **Search Execution**: Performs vector search using the embedded query
4. **Result Formatting**: Structures and ranks search results

## Security Notes

- The server binds to all interfaces (0.0.0.0) by default; in production, consider restricting this
- The API doesn't implement authentication; if exposed publicly, add API key validation
- OpenAI API keys are loaded from environment variables; ensure they're properly secured

## Extending the Tool

The current implementation provides basic search functionality. To extend it:

1. Update the `TOOL_DESCRIPTOR` with additional parameters
2. Modify the `handle_call` function to process new parameters
3. Update the search engine to support the new functionality

For example, adding a new feature to summarize search results would involve:
- Adding a "summarize" parameter to the input schema
- Modifying the call handler to process this parameter
- Implementing the summarization logic

## Additional Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [MCP Specification](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agents-mcp-101)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)