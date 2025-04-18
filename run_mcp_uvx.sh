#!/bin/bash
# Script to run PyTorch Documentation Search MCP server with UVX

# Set current directory to script location
cd "$(dirname "$0")"

# Source conda to ensure it's available
source ~/miniconda3/etc/profile.d/conda.sh

# Activate the conda environment
conda activate pytorch_docs_search

# Run the server with UVX
uvx run mcp-server-pytorch