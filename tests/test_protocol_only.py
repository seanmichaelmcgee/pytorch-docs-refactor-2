#!/usr/bin/env python3
"""
Test script to verify the protocol implementation without database dependencies.
"""

import json
from typing import Dict, Any

def mock_search_handler(args: Dict[str, Any]) -> Dict[str, Any]:
    """Mock search handler that returns pre-defined results."""
    query = args.get("query", "default query")
    return {
        "results": [
            {
                "title": "DataLoader Example",
                "snippet": "This is a PyTorch DataLoader example.",
                "source": "https://pytorch.org/docs/stable/data.html",
                "chunk_type": "code",
                "score": 0.95
            },
            {
                "title": "PyTorch Basics",
                "snippet": "Another PyTorch sample.",
                "source": "https://pytorch.org/docs/stable/intro.html",
                "chunk_type": "text",
                "score": 0.85
            }
        ],
        "query": query,
        "count": 2
    }

def test_protocol_handler():
    """Test the protocol handler with a mock search function."""
    from ptsearch.protocol import MCPProtocolHandler
    
    # Create handler with mock search
    handler = MCPProtocolHandler(mock_search_handler)
    
    # Test initialize
    init_message = {
        "jsonrpc": "2.0",
        "id": "test-init",
        "method": "initialize"
    }
    
    init_response = handler.process_message(json.dumps(init_message))
    init_response_data = json.loads(init_response)
    
    print(f"Initialize response: {json.dumps(init_response_data, indent=2)}")
    assert init_response_data["id"] == "test-init"
    assert "capabilities" in init_response_data["result"]
    
    # Test list_tools
    list_message = {
        "jsonrpc": "2.0",
        "id": "test-list",
        "method": "list_tools"
    }
    
    list_response = handler.process_message(json.dumps(list_message))
    list_response_data = json.loads(list_response)
    
    print(f"List tools response: {json.dumps(list_response_data, indent=2)}")
    assert list_response_data["id"] == "test-list"
    assert "tools" in list_response_data["result"]
    
    # Get tool name
    tool_name = list_response_data["result"]["tools"][0]["name"]
    
    # Test call_tool
    call_message = {
        "jsonrpc": "2.0",
        "id": "test-call",
        "method": "call_tool",
        "params": {
            "tool": tool_name,
            "args": {
                "query": "How to use DataLoader"
            }
        }
    }
    
    call_response = handler.process_message(json.dumps(call_message))
    call_response_data = json.loads(call_response)
    
    print(f"Call tool response: {json.dumps(call_response_data, indent=2)}")
    assert call_response_data["id"] == "test-call"
    assert "result" in call_response_data["result"]
    assert "results" in call_response_data["result"]["result"]
    
    print("\n✅ Protocol handler test passed!")
    return True

def main():
    """Run protocol tests."""
    try:
        test_protocol_handler()
        return 0
    except Exception as e:
        print(f"\n❌ Protocol test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())