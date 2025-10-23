# Slack MCP Server for Databricks Apps

A Model Context Protocol (MCP) server for Slack, deployable on Databricks Apps. This server provides comprehensive Slack workspace integration including message history, thread replies, search, and channel management.

## Features

- **Message History**: Fetch messages from channels and DMs with smart pagination
- **Thread Replies**: Get threaded conversations
- **Message Search**: Search messages with advanced filters
- **Channel Management**: List and browse all workspace channels
- **User Directory**: Access workspace user information
- **Message Posting**: Send messages to channels (configurable)
- **Token Management UI**: Update Slack tokens directly from the web interface
- **Databricks Apps Ready**: Fully compatible with Databricks Apps deployment

## Tools

### 1. conversations_history
Get messages from a channel or DM by channel_id.

**Parameters:**
- `channel_id` (string, required): Channel ID (Cxxxxxxxxxx) or name (#general, @username_dm)
- `include_activity_messages` (boolean, default: false): Include join/leave messages
- `cursor` (string, optional): Pagination cursor
- `limit` (string, default: "1d"): Time range (1d, 7d, 30d) or message count (50)

### 2. conversations_replies
Get thread messages by channel_id and thread timestamp.

**Parameters:**
- `channel_id` (string, required): Channel ID or name
- `thread_ts` (string, required): Thread timestamp (e.g., "1234567890.123456")
- `include_activity_messages` (boolean, default: false): Include activity messages
- `cursor` (string, optional): Pagination cursor
- `limit` (string, default: "1d"): Time range or message count

### 3. conversations_add_message
Post a message to a channel or thread.

**Parameters:**
- `channel_id` (string, required): Channel ID or name
- `payload` (string, required): Message text
- `thread_ts` (string, optional): Thread timestamp to reply to
- `content_type` (string, default: "text/markdown"): Content type

**Note:** Disabled by default. Enable by setting `SLACK_MCP_ADD_MESSAGE_TOOL` environment variable.

### 4. conversations_search_messages
Search messages with filters.

**Parameters:**
- `search_query` (string): Search text or Slack message URL
- `filter_in_channel` (string): Channel ID or name
- `filter_in_im_or_mpim` (string): DM/MPIM ID or name
- `filter_users_from` (string): Filter by sender
- `filter_date_before` (string): Date filter (YYYY-MM-DD)
- `filter_date_after` (string): Date filter (YYYY-MM-DD)
- `cursor` (string): Pagination cursor
- `limit` (int, default: 20): Max results (1-100)

### 5. channels_list
Get list of channels.

**Parameters:**
- `channel_types` (string, required): Comma-separated types: mpim, im, public_channel, private_channel
- `sort` (string, optional): "popularity" sorts by member count
- `limit` (int, default: 100): Max results (1-1000)
- `cursor` (string, optional): Pagination cursor

## Resources

### slack://workspace/channels
CSV directory of all channels with ID, name, topic, purpose, and member count.

### slack://workspace/users
CSV directory of all users with ID, username, and real name.

## Installation & Deployment

### Prerequisites

- Python 3.10 or higher
- Python `pip` package manager (usually included with Python)
- Databricks CLI (for Databricks deployment)
- Slack workspace access

### Authentication Setup

You need Slack API credentials. Choose one method:

#### Option 1: OAuth Token (Recommended)
Set environment variable:
```bash
export SLACK_MCP_XOXP_TOKEN="xoxp-your-token-here"
```

#### Option 2: Browser Tokens (Stealth Mode)
Set both environment variables:
```bash
export SLACK_MCP_XOXC_TOKEN="xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34"
export SLACK_MCP_XOXD_TOKEN="xoxd-your-token-here"
```

For this deployment, the xoxc token is already configured as shown above.

### Local Development

1. **Install dependencies:**
```bash
pip install -e .
```

2. **Set environment variables:**
```bash
export SLACK_MCP_XOXC_TOKEN="xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34"
export SLACK_MCP_XOXD_TOKEN="xoxd-your-d-token"  # Get this from your Slack browser cookies
```

3. **Run the server:**
```bash
# For stdio mode (Claude Desktop)
slack-mcp-server

# For Databricks Apps mode with FastAPI
slack-mcp-server-databricks
# Or alternatively:
python -m slack_mcp_server.main
```

The server will start at `http://localhost:8000` with:
- Landing page at `/`
- Token configuration UI at `/config`
- MCP endpoint at `/mcp/`

### Token Management UI

The server includes a built-in web interface for managing Slack tokens:

1. **Access the UI**: Navigate to `http://localhost:8000/config` (or `/config` on your deployed app)
2. **View Current Status**: See which tokens are currently configured (tokens are masked for security)
3. **Update Tokens**: Enter new xoxc and xoxd tokens and submit
4. **Automatic Reload**: The server automatically updates the `.env` file and reloads configuration

This is especially useful in Databricks Apps where you can update tokens without redeploying the application or accessing environment variable settings.

### Deploying to Databricks Apps

This MCP server is designed to run on Databricks Apps using the bundle deployment method.

#### Step 1: Configure Databricks CLI

```bash
# Set your Databricks profile
export DATABRICKS_CONFIG_PROFILE=<your-profile-name>

# Login to Databricks
databricks auth login --profile "$DATABRICKS_CONFIG_PROFILE"
```

#### Step 2: Build the Wheel

```bash
# Build the Python wheel package
python -m pip install hatchling
python -m hatchling build -t wheel
```

This creates a `.whl` file in the `dist/` directory and a `.build/` directory with the deployment artifacts.

#### Step 3: Deploy with Databricks Bundle

```bash
# Deploy the bundle
databricks bundle deploy

# Run the app
databricks bundle run slack-mcp-server-databricks
```

#### Alternative: Manual Deployment with Databricks Apps CLI

```bash
# Get your Databricks username
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)

# Create the app
databricks apps create slack-mcp-server-databricks

# Sync files to workspace
databricks sync . "/Users/$DATABRICKS_USERNAME/slack-mcp-server-databricks"

# Deploy the app
databricks apps deploy slack-mcp-server-databricks \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/slack-mcp-server-databricks"
```

#### Step 4: Configure Environment Variables in Databricks

After deployment, configure the Slack tokens in your Databricks App settings:

1. Go to Databricks Apps UI
2. Select your `slack-mcp-server-databricks` app
3. Add environment variables:
   - `SLACK_MCP_XOXC_TOKEN`: `xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34`
   - `SLACK_MCP_XOXD_TOKEN`: Your xoxd token from Slack cookies

#### Step 5: Access Your Deployed App

Once deployed, your app will have a URL like:
```
https://<workspace>.cloud.databricks.com/apps/<app-id>
```

The MCP endpoint will be at:
```
https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/
```

### Connecting to the Deployed Server

Use the Streamable HTTP transport with Databricks OAuth:

```python
from databricks.sdk import WorkspaceClient
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession

client = WorkspaceClient()

async def main():
    app_url = "https://your.databricks.com/apps/your-app-id/mcp/"
    
    async with connect(app_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Use the conversation_history tool
            result = await session.call_tool(
                "conversations_history", 
                {"channel_id": "#general", "limit": "10"}
            )
            print(result)
```

**Important:** The URL must end with `/mcp/` (including the trailing slash).

## Environment Variables

| Variable | Required? | Default | Description |
|----------|-----------|---------|-------------|
| `SLACK_MCP_XOXC_TOKEN` | Yes* | - | Slack browser token (xoxc-...) |
| `SLACK_MCP_XOXD_TOKEN` | Yes* | - | Slack browser cookie d (xoxd-...) |
| `SLACK_MCP_XOXP_TOKEN` | Yes* | - | User OAuth token (xoxp-...) - alternative to xoxc/xoxd |
| `SLACK_MCP_ADD_MESSAGE_TOOL` | No | - | Enable message posting (set to "true" or comma-separated channel IDs) |
| `SLACK_MCP_ADD_MESSAGE_MARK` | No | - | Auto-mark posted messages as read |
| `SLACK_MCP_ADD_MESSAGE_UNFURLING` | No | - | Enable link unfurling for posted messages |

*You need either `SLACK_MCP_XOXP_TOKEN` **or** both `SLACK_MCP_XOXC_TOKEN` and `SLACK_MCP_XOXD_TOKEN`.

## Project Structure

```
.
├── src/
│   └── slack_mcp_server/
│       ├── __init__.py          # Package initialization
│       ├── server.py            # Main MCP server implementation
│       ├── app.py               # FastAPI wrapper for Databricks
│       ├── main.py              # Uvicorn entry point
│       └── static/
│           └── index.html       # Landing page
├── hooks/
│   └── apps_build.py            # Build hook for Databricks Apps
├── pyproject.toml               # Project dependencies and metadata
├── databricks.yml               # Databricks bundle configuration
├── app.yaml                     # App command configuration
├── .python-version              # Python version specification
└── README.md                    # This file
```

## Testing Locally

Test the MCP server locally before deploying:

```bash
# Test with MCP Inspector
mcp dev src/slack_mcp_server/server.py

# Test with uvicorn (FastAPI mode)
uvicorn slack_mcp_server.app:app --reload

# Test specific tool
python -c "
from slack_mcp_server.server import slack_server
import asyncio

class FakeContext:
    async def info(self, msg): print(f'INFO: {msg}')
    async def error(self, msg): print(f'ERROR: {msg}')

async def test():
    ctx = FakeContext()
    await slack_server.initialize(ctx)
    print('Server initialized successfully!')

asyncio.run(test())
"
```

## Troubleshooting

### Authentication Errors

If you get authentication errors:
1. Verify your tokens are correctly set
2. Check token permissions in Slack workspace
3. Ensure tokens haven't expired

### Databricks Deployment Issues

If deployment fails:
1. Check `databricks bundle validate` output
2. Verify your Databricks CLI is configured correctly
3. Ensure you have permissions to create apps in the workspace

### Build Errors

If the build fails:
1. Ensure `hatchling` is installed: `pip install hatchling`
2. Check Python version: Should be 3.10+
3. Clear cache: `rm -rf .build dist`

## Security

- Never commit tokens or credentials to version control
- Use environment variables for sensitive data
- Keep `.env` files secure and private
- The `conversations_add_message` tool is disabled by default for safety

## Contributing

Issues and pull requests are welcome! Some areas for improvement:
- Enhanced error handling and retry logic
- Rate limiting for API calls
- Caching optimization
- Additional Slack API features

## License

Licensed under MIT - see LICENSE file. This is not an official Slack product.

## Credits

Based on the original [Slack MCP Server](https://github.com/korotovsky/slack-mcp-server) by korotovsky.
Converted to Python and adapted for Databricks Apps deployment.
