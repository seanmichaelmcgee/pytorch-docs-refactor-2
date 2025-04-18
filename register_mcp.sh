#!/bin/bash
# This script registers the PyTorch Documentation Search MCP server with Claude CLI

# Get the absolute path to the run script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUN_SCRIPT="${SCRIPT_DIR}/run_mcp.sh"

# Register with Claude CLI using stdio transport
echo "Registering PyTorch Documentation Search MCP server with Claude CLI..."
claude mcp add pytorch_search stdio "${RUN_SCRIPT}"

echo "Registration complete. You can now use the tool with Claude."
echo "To test your installation, ask Claude Code about PyTorch:"
echo "claude"
echo "Then type: How do I use PyTorch DataLoader for custom datasets?"