# MCP Integration Guide

This document describes how to use the PyTorch Documentation Search Tool with Claude via Model Context Protocol (MCP) integration.

## Overview

The Model Context Protocol is Anthropic's standard for tool integration with Claude. This enables Claude to use external tools, including the PyTorch Documentation Search tool.

## Installation Options

### Option 1: UVX Installation (Recommended)

The simplest way to install and use the PyTorch Documentation Search tool is via UVX, which provides a direct execution model:

```bash
# First, make sure you have the UVX package manager
pip install uvx

# Add the tool to Claude CLI directly from GitHub
claude mcp add pytorch_search uvx mcp-server-pytorch

# Or from a local path
claude mcp add pytorch_search uvx /path/to/pytorch-docs-search
```

### Option 2: Python Package Installation

Alternatively, you can install the package via pip:

```bash
pip install mcp-server-pytorch

# Register with Claude CLI
claude mcp add pytorch_search python -m mcp_server_pytorch
```

### Option 3: Running as a Server (Legacy SSE Mode)

If you prefer to run the tool as a server using SSE transport:

```bash
# Start the server
python -m mcp_server_pytorch --transport sse

# Then in another terminal
claude mcp add --transport sse pytorch_search http://localhost:5000/events
```

## Implementation Details

### Transports

The tool supports two transport mechanisms:

1. **STDIO Transport (Default)**
   - Direct execution model
   - No server to maintain
   - Runs on demand

2. **SSE Transport (Alternative)**
   - Server-based model
   - Runs continuously
   - Required for some integration scenarios

### Tool Definition

The PyTorch documentation search tool is defined with the following parameters:

- **Tool Name**: `search_pytorch_docs`
- **Type**: `function`
- **Description**: "Search PyTorch documentation or examples. Call when the user asks about a PyTorch API, error message, best-practice or needs a code snippet."

### Input Parameters

- `query` (string, required): The search query
- `num_results` (integer, optional, default=5): Number of results to return
- `filter` (string, optional, enum=["code", "text", ""]): Filter results by type

### Response Format

```json
{
  "query": "tensor operations",
  "results": [
    {
      "title": "torch.Tensor",
      "chunk_type": "text",
      "source": "https://pytorch.org/docs/stable/tensors.html",
      "score": 0.923,
      "snippet": "A PyTorch Tensor is a multi-dimensional matrix containing elements of a single data type..."
    },
    ...
  ]
}
```

## Using with Claude Code

Once registered, you can simply ask Claude Code about PyTorch:

```
How do I create a custom Dataset in PyTorch?
What's the difference between torch.nn.Module and torch.nn.functional?
Show me how to implement a custom autograd function.
```

Claude will automatically call the PyTorch documentation search tool when appropriate.

## Debugging and Verification

### Verify Registration

```bash
# List registered MCP tools
claude mcp list
```

You should see `search_pytorch_docs` in the list of available tools.

### Test Direct Invocation

```bash
# Test the tool directly
claude run tool search_pytorch_docs --input '{"query": "How to use DataLoader"}'
```

### MCP Inspector (for advanced debugging)

For detailed debugging of the MCP protocol, you can use the MCP inspector:

```bash
# Install the inspector
npm install -g @modelcontextprotocol/inspector

# Use it with UVX
npx @modelcontextprotocol/inspector uvx mcp-server-pytorch

# Or with direct Python execution
npx @modelcontextprotocol/inspector python -m mcp_server_pytorch
```

## Troubleshooting

### Common Issues

1. **API Key Missing**
   - Error: "OPENAI_API_KEY not found"
   - Solution: Set the OPENAI_API_KEY environment variable or add it to a .env file

2. **Tool Not Found**
   - Error: "Tool not found"
   - Solution: Verify registration with `claude mcp list`

3. **Connection Refused (SSE mode)**
   - Error: "Connection refused"
   - Solution: Ensure the server is running on the specified port

## Architecture

The MCP implementation follows a simple flow:

1. **Initialization**: Sets up search components (database, embedding generator, search engine)
2. **Transport Handler**: Processes messages based on transport type (stdio or SSE)
3. **Tool Definition**: Maintains a consistent tool descriptor across both transports
4. **Search Execution**: Calls into the main search engine with query parameters
5. **Response Formatting**: Returns formatted search results to Claude

## Additional Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [MCP Specification](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agents-mcp-101)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)