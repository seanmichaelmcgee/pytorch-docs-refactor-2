# PyTorch Documentation Search Tool

A streamlined semantic search system for PyTorch documentation that understands both code and text, providing relevant results for technical queries.

## Overview

This tool enables developers to efficiently search PyTorch documentation using natural language or code-based queries. It preserves the integrity of code examples, understands programming patterns, and intelligently ranks results based on query intent.

## Key Features

- Code-aware document processing that preserves code block integrity
- Semantic search powered by OpenAI embeddings
- Query intent detection for better results ranking
- Basic embedding caching for efficiency
- Claude Code integration through Model Context Protocol (MCP)
- Modular architecture with support for multiple transport methods
- Flexible data directory configuration
- UVX integration for seamless deployment

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key
- Conda environment (recommended)

### Installation

#### Option 1: Direct Installation with UVX (Recommended)

Using UVX provides a seamless integration with Claude Code:

```bash
# First, make sure you have the UVX package manager
pip install uvx

# Export your OpenAI API key (required)
export OPENAI_API_KEY="your-api-key"

# Add the tool to Claude CLI using the correct tool name
claude mcp add search_pytorch_docs http://localhost:5000/events --transport sse

# Or directly with UVX
uvx mcp-server-pytorch --transport sse --host 127.0.0.1 --port 5000 --data-dir ./data

# Verify it's registered
claude mcp list
```

#### Option 2: Traditional Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pytorch-docs-search.git
   cd pytorch-docs-search
   ```

2. Set up the Conda environment:
   ```bash
   conda env create -f environment.yml
   conda activate pytorch_docs_search
   ```

3. Set up your environment variables:
   ```bash
   cp .env.example .env
   # Edit .env file to add your OpenAI API key
   ```

4. Register with Claude CLI:
   ```bash
   # If you want to use direct execution (stdio)
   ./register_mcp.sh
   
   # If you want to use server mode (SSE)
   # First, start the server with data directory
   python -m mcp_server_pytorch --transport sse --data-dir ./data
   # Then in another terminal
   claude mcp add search_pytorch_docs http://localhost:5000/events --transport sse
   ```

## Processing Documentation

Process your PyTorch documentation into chunks:

```bash
ptsearch process --docs-dir /path/to/pytorch/docs
```

### Generating Embeddings

Generate embeddings for the processed chunks:

```bash
ptsearch embed --input-file ./data/chunks.json
```

### Indexing to Database

Load the embeddings into the ChromaDB vector database:

```bash
ptsearch index --input-file ./data/chunks_with_embeddings.json
```

## Using with Claude Code

Once registered, you can simply ask Claude Code about PyTorch:

```
How do I create a custom Dataset in PyTorch?
What's the difference between torch.nn.Module and torch.nn.functional?
Show me how to implement a custom autograd function.
```

Claude will automatically call the PyTorch documentation search tool when appropriate.

## Running Tests

Run the protocol test to verify the MCP implementation:

```bash
# Test the STDIO transport
python -m tests.test_mcp_protocol

# Run unit tests
pytest tests/unit/
```

## Architecture

The tool uses a modular architecture with these components:

### Core Components

- **Core** (`ptsearch/core/`): Core functionality for search and embedding
  - `database.py`: ChromaDB integration for vector search
  - `embedding.py`: OpenAI API integration for embedding generation
  - `search.py`: Main search engine with query processing
  - `formatter.py`: Result formatting and ranking

- **Transport** (`ptsearch/transport/`): MCP transport implementations
  - `base.py`: Base transport interface
  - `stdio.py`: STDIO transport for direct execution
  - `sse.py`: SSE transport for server mode

- **Protocol** (`ptsearch/protocol/`): MCP protocol handling
  - `descriptor.py`: Tool descriptor definition
  - `handler.py`: MCP protocol message handling

- **Config** (`ptsearch/config/`): Configuration management
  - `settings.py`: Settings with environment validation

- **Utils** (`ptsearch/utils/`): Shared utilities
  - `logging.py`: Enhanced logging with context
  - `error.py`: Error hierarchy and formatting

## Configuration

The tool can be configured through environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key
- `PTSEARCH_EMBEDDING_MODEL`: Embedding model to use (default: text-embedding-3-large)
- `PTSEARCH_MAX_RESULTS`: Default number of search results (default: 5)
- `PTSEARCH_DB_DIR`: ChromaDB storage location (default: ./data/chroma_db)
- `PTSEARCH_COLLECTION_NAME`: Name of the ChromaDB collection (default: pytorch_docs)
- `PTSEARCH_CACHE_DIR`: Embedding cache directory (default: ./data/embedding_cache)
- `MCP_LOG_FILE`: Log file path for MCP server (default: mcp_server.log)

## Manual Search

You can also search the documentation directly using the command-line interface:

```bash
ptsearch search "How to implement a custom autograd function"
```

Or use interactive mode:

```bash
ptsearch search --interactive
```

## Troubleshooting

### Common Issues

1. **Connection Timeout or ConfigError**
   - Ensure your OPENAI_API_KEY is correctly set and exported
   - Check if the ChromaDB database has been properly initialized
   - Verify the data directory exists and contains required files
   - Verify your environment has all required dependencies

2. **No Results Returned**
   - Make sure you've processed and indexed documentation
   - Ensure the --data-dir parameter points to the correct location
   - Check the server logs for any errors

3. **Tool Not Found**
   - Verify the tool is correctly registered with `claude mcp list`
   - Make sure you're using the exact name "search_pytorch_docs" when registering
   - Check that the server is running when attempting to use the tool

4. **UVX Integration Issues**
   - Ensure the .uvx/tool.json file is properly configured
   - Verify that the OPENAI_API_KEY is set in the environment
   - Try using the direct command: `uvx mcp-server-pytorch --transport sse --data-dir ./data`

### Checking Logs

By default, the server logs to stderr and to a file named `mcp_server.log`. Check this file for detailed information about any issues.

### Recent Fixes

Several critical issues have been fixed in the latest update:
- UVX configuration has been corrected for proper integration
- OpenAI API key validation has been improved with clear error messages
- A --data-dir parameter has been added to specify where data is stored
- Tool name registration has been standardized to match the descriptor
- Documentation has been updated with clearer instructions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [OpenAI API](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB](https://docs.trychroma.com/)
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [Claude Code](https://docs.anthropic.com/en/docs/agents-and-tools/claude-code/overview)
- [Model Context Protocol](https://docs.anthropic.com/en/docs/agents-and-tools/claude-agents-mcp-101)