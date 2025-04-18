# MCP Integration Guide

This document describes how to use the PyTorch Documentation Search Tool with Claude via Model Context Protocol (MCP) integration.

## Overview

The Model Context Protocol is Anthropic's standard for tool integration with Claude. This enables Claude to use external tools, including the PyTorch Documentation Search tool.

## Server Implementation

The `ptsearch/mcp.py` module implements an MCP-compatible server with the following key components:

1. **Tool Descriptor**: Defines the tool's capabilities, parameters, and endpoint
2. **SSE Endpoint**: Provides tool discovery via server-sent events
3. **Call Handler**: Processes Claude's requests to search the documentation

### STDIO Transport Support

In addition to the SSE transport, the `ptsearch/stdio.py` module provides STDIO transport support, allowing direct integration with Claude without needing to run a separate server process.

## Setup and Usage

### 1. Environment Setup

You must have an OpenAI API key for embedding generation.

```bash
# Setup environment with conda
conda env create -f environment.yml
conda activate pytorch_docs_search

# Set API key (or add to .env file)
export OPENAI_API_KEY=your_api_key_here
```

### 2. Running the Server (SSE Transport)

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

### 3. Running with STDIO Transport

```bash
# Direct execution
mcp-server-pytorch-stdio

# Or using the CLI
ptsearch stdio
```

### 4. Registering the Tool with Claude CLI

For SSE transport (server mode):

```bash
claude mcp add --transport sse pytorch_search http://localhost:5000/events
```

For stdio transport (direct execution):

```bash
claude mcp add --transport stdio pytorch_search mcp-server-pytorch-stdio
```

### 5. Verify Registration

```bash
claude mcp list
```

You should see `search_pytorch_docs` in the list of available tools.

### 6. Using the Tool with Claude

```bash
# Start Claude with the MCP tool available
claude

# Or use a direct command
claude run tool search_pytorch_docs --input '{"query": "How to use DataLoader"}'
```

Example conversation with Claude:

```
User: How do I create a DataLoader in PyTorch?

Claude: I'll search the PyTorch documentation to get accurate information on creating a DataLoader.

[Tool use: search_pytorch_docs]
I found information on creating a DataLoader in PyTorch:

To create a DataLoader in PyTorch, you need to:
1. First create a Dataset object (either a custom dataset by subclassing torch.utils.data.Dataset or use existing datasets)
2. Pass the dataset to DataLoader constructor with parameters like batch_size, shuffle, num_workers

Basic example:
```python
from torch.utils.data import Dataset, DataLoader

# Create a dataset
dataset = YourDataset(...)  # Custom dataset or built-in dataset

# Create a DataLoader
dataloader = DataLoader(
    dataset=dataset,       # The dataset to load data from
    batch_size=32,         # Number of samples per batch
    shuffle=True,          # Whether to shuffle the data
    num_workers=4,         # Number of subprocesses for data loading
    drop_last=False        # Whether to drop the last incomplete batch
)

# Iterate through the dataloader
for batch_idx, (data, target) in enumerate(dataloader):
    # Your training loop here
    ...
```

Key parameters:
- batch_size: how many samples per batch to load
- shuffle: whether to reshuffle at every epoch
- num_workers: how many subprocesses to use for data loading
- drop_last: drop the last incomplete batch if dataset size is not divisible by batch_size
- collate_fn: custom function for merging samples into a batch

Is there a specific aspect of DataLoader you'd like me to explain further?
```

## Using with UVX Package Manager

The tool can be installed using the Utility Vector eXchange (UVX) package manager.

```bash
# Install directly
uvx install path/to/pytorch-docs-search

# Or install from GitHub
uvx install github:yourusername/pytorch-docs-search
```

## Tool Details

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

## Troubleshooting

### Common Issues

1. **API Key Missing**
   - Error: "OPENAI_API_KEY not found"
   - Solution: Set the OPENAI_API_KEY environment variable or add it to a .env file

2. **Connection Refused**
   - Error: "Connection refused"
   - Solution: Ensure the server is running on the specified port

3. **Tool Not Found**
   - Error: "Tool not found"
   - Solution: Verify registration with `claude mcp list`

### Logs

All API requests are logged with detailed information. Common issues you might encounter are mentioned above.

## Architecture

The MCP server implementation in `mcp.py` follows a simple flow:

1. **Tool Discovery**: `/events` endpoint for SSE-based tool registration
2. **Call Handling**: `/tools/call` endpoint processes tool invocations
3. **Search Execution**: Calls into the main search engine

The STDIO implementation in `stdio.py` follows a similar pattern but uses stdin/stdout for communication instead of HTTP.

## Customization and Extension

Several extension points are available for customization:

1. **Tool Descriptor**: Modify properties in the `TOOL_DESCRIPTOR` to change the tool behavior
2. **Filtering**: Update filter options to provide more specific results
3. **Result Format**: Modify the `ResultFormatter` class to change the presentation of results

For example, adding a new feature to summarize search results would involve:

- Adding a `summarize` parameter to the tool input schema
- Modifying the call handler to process this parameter
- Implementing the summarization logic

## Additional Resources

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [MCP Specification](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agents-mcp-101)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)