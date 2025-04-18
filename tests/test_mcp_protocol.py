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
import argparse

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

def test_protocol(module_name="mcp_server_pytorch", timeout=30):
    """Run MCP protocol test with the given server module."""
    # Start the MCP server
    env = os.environ.copy()
    if "OPENAI_API_KEY" not in env:
        print("Error: OPENAI_API_KEY environment variable not set", file=sys.stderr)
        return 1
        
    # Set log file to stderr for testing
    env["MCP_LOG_FILE"] = "/dev/stderr"
    
    print(f"Starting MCP server: {module_name}", file=sys.stderr)
    proc = subprocess.Popen(
        ["python", "-m", module_name, "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    
    # Set timeout for process
    start_time = time.time()
    
    try:
        # Check if process is still alive
        if proc.poll() is not None:
            print(f"Process exited with code {proc.returncode}", file=sys.stderr)
            return 1
        
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
        
        # Get the tool name
        tool_name = tools[0]["name"]
        
        # Send a call_tool request with a simple query
        send_message(proc, {
            "jsonrpc": "2.0",
            "id": "3",
            "method": "call_tool",
            "params": {
                "tool": tool_name,
                "args": {
                    "query": "How to use PyTorch DataLoader",
                    "num_results": 1
                }
            }
        })
        
        # Read call_tool response
        call_response = read_message(proc)
        if not call_response or "result" not in call_response:
            print("Call tool failed", file=sys.stderr)
            return 1
        
        # Verify search results
        result = call_response["result"].get("result", {})
        if "results" not in result or not isinstance(result["results"], list):
            print("Invalid search results format", file=sys.stderr)
            return 1
        
        # Success
        print("MCP protocol test passed!", file=sys.stderr)
        return 0
        
    except Exception as e:
        print(f"Error during test: {e}", file=sys.stderr)
        return 1
    finally:
        # Clean up
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except:
            proc.kill()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test MCP protocol implementation")
    parser.add_argument("--module", default="mcp_server_pytorch", 
                      help="Server module to test (default: mcp_server_pytorch)")
    parser.add_argument("--timeout", type=int, default=30,
                      help="Timeout in seconds (default: 30)")
    
    args = parser.parse_args()
    sys.exit(test_protocol(args.module, args.timeout))