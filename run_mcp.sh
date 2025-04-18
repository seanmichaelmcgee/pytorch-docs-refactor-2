#!/bin/bash
# Script to run PyTorch Documentation Search MCP server with stdio transport

# Set current directory to script location
cd "$(dirname "$0")"

# Enable debug mode
set -x

# Source conda to ensure it's available
if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/miniconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    source "$HOME/anaconda3/etc/profile.d/conda.sh"
else
    echo "Could not find conda.sh. Please ensure Miniconda or Anaconda is installed."
    exit 1
fi

# Activate the conda environment
conda activate pytorch_docs_search

# Run the server with stdio transport
exec python -m mcp_server_pytorch --transport stdio