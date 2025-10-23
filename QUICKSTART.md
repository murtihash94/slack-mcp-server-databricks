# Quick Start Guide - Slack MCP Server on Databricks

Get your Slack MCP Server running on Databricks Apps in 5 minutes!

## Prerequisites

- Databricks workspace access
- Databricks CLI installed
- Slack workspace access
- The provided xoxc token: `xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34`

## Quick Steps

### 1. Get Your Slack xoxd Token

1. Open Slack in your browser at https://app.slack.com
2. Press F12 to open Developer Tools
3. Go to: Application → Cookies → https://app.slack.com
4. Find cookie named `d` (not `d-s`)
5. Copy its value (starts with `xoxd-`)

### 2. Configure Databricks

```bash
# Login to Databricks
databricks auth login

# Verify authentication  
databricks current-user me
```

### 3. Deploy

```bash
# Clone the repo (if not already)
git clone https://github.com/murtihash94/slack-mcp-server-databricks
cd slack-mcp-server-databricks

# Build the package
pip install uv
uv build --wheel

# Deploy to Databricks
databricks bundle deploy
```

### 4. Configure Environment Variables

In Databricks UI:
1. Go to Apps → slack-mcp-server-databricks
2. Add environment variables:
   - `SLACK_MCP_XOXC_TOKEN`: `xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34`
   - `SLACK_MCP_XOXD_TOKEN`: Your token from Step 1
3. Save and restart the app

### 5. Test Your Deployment

Visit your app URL: `https://<workspace>.cloud.databricks.com/apps/<app-id>/`

You should see the landing page with "Server is running" status!

## MCP Endpoint

Your MCP endpoint URL:
```
https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/
```

Use this URL to connect from:
- Claude Desktop
- Python MCP clients
- Any MCP-compatible application

## Quick Test with Python

```python
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession
import asyncio

async def test():
    app_url = "https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/"
    
    async with connect(app_url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Get channel list
            result = await session.call_tool(
                "channels_list",
                {"channel_types": "public_channel", "limit": 5}
            )
            print(result)

asyncio.run(test())
```

## Available Tools

- `conversations_history` - Get channel messages
- `conversations_replies` - Get thread messages  
- `conversations_add_message` - Post messages
- `conversations_search_messages` - Search messages
- `channels_list` - List channels

## Resources

- `slack://workspace/channels` - Channel directory (CSV)
- `slack://workspace/users` - User directory (CSV)

## Troubleshooting

### App won't start
- Check environment variables are set correctly
- Verify both xoxc and xoxd tokens are valid
- Check app logs in Databricks UI

### Authentication errors
- Try getting fresh tokens from Slack
- Verify you have access to the Slack workspace
- Check token format (xoxc- and xoxd- prefixes)

### Can't connect to MCP endpoint
- Ensure URL ends with `/mcp/` (with trailing slash)
- Verify app is running (not stopped)
- Check network access to Databricks

## Need More Help?

- **Full Documentation**: [DATABRICKS_README.md](DATABRICKS_README.md)
- **Deployment Guide**: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- **Issues**: [GitHub Issues](https://github.com/murtihash94/slack-mcp-server-databricks/issues)

## Next Steps

1. ✅ Test all available tools
2. ✅ Connect from Claude Desktop
3. ✅ Build LLM applications using the MCP server
4. ✅ Enable message posting if needed
5. ✅ Set up monitoring and logging

Happy building! 🎉
