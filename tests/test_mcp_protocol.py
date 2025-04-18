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