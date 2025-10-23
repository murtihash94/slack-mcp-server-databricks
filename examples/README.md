# Examples

This directory contains example code for using the Slack MCP Server.

## Available Examples

### example_usage.py

Comprehensive Python example showing how to:
- Connect to the MCP server
- List available tools and resources
- Fetch channel history
- Search messages
- List channels
- Get thread replies
- Post messages (when enabled)
- Access CSV resources (channels and users)

## Running the Examples

### Prerequisites

Install the MCP Python SDK:
```bash
pip install mcp
```

### Update the Configuration

Edit `example_usage.py` and update the `APP_URL` variable with your Databricks app URL:
```python
APP_URL = "https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/"
```

### Run the Example

```bash
python example_usage.py
```

## Example Output

```
Connecting to Slack MCP Server at: https://...
Initializing MCP session...
✓ Connected successfully!

=== Available Tools ===
- conversations_history: Get messages from a channel or DM
- conversations_replies: Get thread messages
- conversations_add_message: Post messages
- conversations_search_messages: Search messages
- channels_list: List channels

=== Listing Channels (limit=5) ===
id,name,topic,purpose,memberCount,cursor
C1234567890,general,General discussion,Company-wide announcements,150,
...

✓ All examples completed successfully!
```

## Customizing the Examples

You can modify the examples to:
- Change channel names
- Adjust message limits
- Add custom search queries
- Filter by specific users
- Post custom messages

## Additional Examples

### Using with Claude Desktop

Add to your Claude Desktop config:
```json
{
  "mcpServers": {
    "slack-databricks": {
      "url": "https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/",
      "transport": "http"
    }
  }
}
```

### Using with LangChain

```python
from langchain.agents import initialize_agent
from langchain_mcp import MCPToolkit

toolkit = MCPToolkit(
    mcp_server_url="https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/"
)

agent = initialize_agent(
    toolkit.get_tools(),
    llm=your_llm,
    agent="zero-shot-react-description"
)

result = agent.run("Get the latest messages from #general channel")
```

## Troubleshooting

### Connection Errors

If you get connection errors:
1. Verify the APP_URL is correct
2. Check that the app is running in Databricks
3. Ensure the URL ends with `/mcp/`

### Authentication Errors

If you get authentication errors:
1. Verify environment variables are set in Databricks
2. Check that Slack tokens are valid
3. Try refreshing the tokens

### Tool Errors

If specific tools fail:
1. Check the tool parameters are correct
2. Verify channel IDs/names exist
3. For message posting, ensure the tool is enabled

## Need Help?

- Check the main [README.md](../README.md)
- Review the [Deployment Guide](../DEPLOYMENT_GUIDE.md)
- Open an [issue](https://github.com/murtihash94/slack-mcp-server-databricks/issues)
