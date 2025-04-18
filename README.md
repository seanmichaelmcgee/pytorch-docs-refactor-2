# PyTorch Documentation Search Tool (Refactored)

A streamlined semantic search system for PyTorch documentation that understands both code and text, providing relevant results for technical queries.

## Overview

This tool enables developers to efficiently search PyTorch documentation using natural language or code-based queries. It preserves the integrity of code examples, understands programming patterns, and intelligently ranks results based on query intent.

## Key Features

- Code-aware document processing that preserves code block integrity
- Semantic search powered by OpenAI embeddings
- Query intent detection for better results ranking
- Basic embedding caching for efficiency
- Claude Code CLI integration

## Getting Started

### Prerequisites

- Python 3.10+
- OpenAI API key
- Conda environment (recommended)

### Installation

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

## Usage

### Processing Documentation

Process your PyTorch documentation into chunks:

```bash
python scripts/process.py --docs-dir /path/to/pytorch/docs
```

### Generating Embeddings

Generate embeddings for the processed chunks:

```bash
python scripts/embed.py --input-file ./data/chunks.json
```

### Indexing to Database

Load the embeddings into the ChromaDB vector database:

```bash
python scripts/index.py --input-file ./data/chunks_with_embeddings.json
```

### Searching Documentation

Search the documentation using the command-line interface:

```bash
python scripts/search.py "How to implement a custom autograd function"
```

Or use interactive mode:

```bash
python scripts/search.py --interactive
```

### Claude Code Integration

Start the MCP-compatible server for Claude Code integration:

```bash
python scripts/server.py
```

Then register the tool with Claude CLI:

```bash
claude mcp add --transport sse pytorch_search http://localhost:5000/events
```

## Project Structure

```
pytorch-docs-search/
├── ptsearch/           # Core library modules
│   ├── config.py       # Configuration module
│   ├── document.py     # Document processing module
│   ├── embedding.py    # Embedding generation module
│   ├── database.py     # Database integration module
│   ├── search.py       # Search functionality module
│   └── formatter.py    # Result formatting module
├── scripts/            # Command-line scripts
│   ├── process.py      # Document processing script
│   ├── embed.py        # Embedding generation script
│   ├── index.py        # Database indexing script
│   ├── search.py       # Search script 
│   └── server.py       # Claude integration server
├── data/               # Data storage
├── environment.yml     # Conda environment
└── README.md           # This file
```

## Configuration

Edit the `.env` file to configure:

- `OPENAI_API_KEY`: Your OpenAI API key
- `CHUNK_SIZE`: Size of document chunks (default: 1000)
- `OVERLAP_SIZE`: Overlap between chunks (default: 200)
- `MAX_RESULTS`: Default number of search results (default: 5)
- `DB_DIR`: ChromaDB storage location (default: ./data/chroma_db)
- `COLLECTION_NAME`: Name of the ChromaDB collection (default: pytorch_docs)

Advanced settings can be modified in `ptsearch/config.py`.

## How It Works

1. **Document Processing**: Uses Tree-sitter to parse markdown and Python files, preserving structure. Chunks documents intelligently, keeping code blocks intact where possible.

2. **Embedding Generation**: Creates vector representations of text using OpenAI's embedding models with basic caching for efficiency.

3. **Vector Database**: Stores embeddings in ChromaDB for efficient similarity search.

4. **Query Processing**: Analyzes queries to determine intent (code vs. concept) and finds the most relevant matches.

5. **Result Ranking**: Boosts code results for code queries and text results for concept queries.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [OpenAI API](https://platform.openai.com/docs/guides/embeddings)
- [ChromaDB](https://docs.trychroma.com/)
- [Tree-sitter](https://tree-sitter.github.io/tree-sitter/)
- [Claude Code CLI](https://www.anthropic.com/claude)