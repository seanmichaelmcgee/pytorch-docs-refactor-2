"""
Unit tests for MCP protocol handler.
"""

import json
import pytest

from ptsearch.protocol import MCPProtocolHandler
from ptsearch.utils.error import ProtocolError


def mock_search_handler(args):
    """Mock search handler for testing."""
    return {"results": [{"title": "Test Result"}], "query": args.get("query", ""), "count": 1}


class TestMCPProtocol:
    """Test class for MCP protocol handler."""
    
    @pytest.fixture
    def protocol_handler(self):
        """Create protocol handler fixture."""
        return MCPProtocolHandler(mock_search_handler)
    
    def test_initialize(self, protocol_handler):
        """Test initialize method."""
        message = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "initialize"
        }
        
        response = protocol_handler.process_message(json.dumps(message))
        response_data = json.loads(response)
        
        assert response_data["id"] == "test"
        assert "result" in response_data
        assert "capabilities" in response_data["result"]
        assert "tools" in response_data["result"]["capabilities"]
    
    def test_list_tools(self, protocol_handler):
        """Test list_tools method."""
        message = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "list_tools"
        }
        
        response = protocol_handler.process_message(json.dumps(message))
        response_data = json.loads(response)
        
        assert response_data["id"] == "test"
        assert "result" in response_data
        assert "tools" in response_data["result"]
        assert len(response_data["result"]["tools"]) == 1
        
        tool = response_data["result"]["tools"][0]
        assert "name" in tool
        assert "schema_version" in tool
        assert tool["type"] == "function"
    
    def test_call_tool(self, protocol_handler):
        """Test call_tool method."""
        # Get the tool descriptor to use the correct name
        list_message = {
            "jsonrpc": "2.0",
            "id": "list",
            "method": "list_tools"
        }
        list_response = protocol_handler.process_message(json.dumps(list_message))
        list_data = json.loads(list_response)
        tool_name = list_data["result"]["tools"][0]["name"]
        
        # Call the tool
        message = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "call_tool",
            "params": {
                "tool": tool_name,
                "args": {
                    "query": "test query"
                }
            }
        }
        
        response = protocol_handler.process_message(json.dumps(message))
        response_data = json.loads(response)
        
        assert response_data["id"] == "test"
        assert "result" in response_data
        assert "result" in response_data["result"]
        assert "results" in response_data["result"]["result"]
        assert response_data["result"]["result"]["query"] == "test query"
    
    def test_invalid_method(self, protocol_handler):
        """Test invalid method."""
        message = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "invalid_method"
        }
        
        response = protocol_handler.process_message(json.dumps(message))
        response_data = json.loads(response)
        
        assert response_data["id"] == "test"
        assert "error" in response_data
        assert response_data["error"]["code"] == -32601
    
    def test_invalid_json(self, protocol_handler):
        """Test invalid JSON."""
        message = "invalid json"
        
        response = protocol_handler.process_message(message)
        response_data = json.loads(response)
        
        assert "error" in response_data
        assert response_data["error"]["code"] == -32700
    
    def test_unknown_tool(self, protocol_handler):
        """Test unknown tool."""
        message = {
            "jsonrpc": "2.0",
            "id": "test",
            "method": "call_tool",
            "params": {
                "tool": "unknown_tool",
                "args": {
                    "query": "test query"
                }
            }
        }
        
        response = protocol_handler.process_message(json.dumps(message))
        response_data = json.loads(response)
        
        assert response_data["id"] == "test"
        assert "error" in response_data
        assert response_data["error"]["code"] == -32602