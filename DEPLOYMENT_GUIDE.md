# Databricks Deployment Guide for Slack MCP Server

This guide walks you through deploying the Slack MCP Server to Databricks Apps step by step.

## Prerequisites

Before you begin, ensure you have:

1. **Databricks Workspace**: Access to a Databricks workspace with permissions to create apps
2. **Databricks CLI**: Installed and configured ([installation guide](https://docs.databricks.com/dev-tools/cli/index.html))
3. **uv Package Manager**: Installed ([installation guide](https://github.com/astral-sh/uv))
4. **Slack Credentials**: Either OAuth token (xoxp) or browser tokens (xoxc + xoxd)
5. **Python 3.10+**: For local testing

## Step 1: Slack Credentials (Already Configured!)

> [!NOTE]
> **Great news!** The repository includes a `.env` file with pre-configured tokens:
> - `SLACK_MCP_XOXC_TOKEN`: Already set
> - `SLACK_MCP_XOXD_TOKEN`: Already set
> 
> You can use these tokens immediately for testing and deployment!

### Using the Pre-configured Tokens

The `.env` file in the repository contains:
```
SLACK_MCP_XOXC_TOKEN="xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34"
SLACK_MCP_XOXD_TOKEN="xoxd-PeFvxXXjFH0Q7YieBDxiePYueb%2FoLwit1Ddrh4Dhgd5ClDl9ZcHmPDiwryc12dSa3SNIXIvYNvrHBs3wwP1gLYhkxuL%2BcmOW%2Bamabd%2FnJ7Hfs51EsmDeLU3TgXWteurlnrP1TJXt7qn3N1JBnbmADgvMmkgq8J2Yo0ZMKCQW7C4WWGxbXQ33LwTIkYSAjnlwNJfyjdRUjTnnGqIRfFz2Ip%2FHh70A"
```

### (Optional) Use Your Own Slack Tokens

If you prefer to use your own tokens:

**For browser tokens (xoxc + xoxd):**

1. Open your Slack workspace in a web browser
2. Open Developer Tools (F12)
3. Go to Application/Storage → Cookies → https://app.slack.com
4. Find the cookie named `d` (not `d-s`) for xoxd token
5. Copy the value and update the `.env` file

### Alternative: Get OAuth token (xoxp):

1. Go to https://api.slack.com/apps
2. Create a new app or select an existing one
3. Go to "OAuth & Permissions"
4. Install the app to your workspace
5. Copy the "User OAuth Token" (starts with `xoxp-`)

## Step 2: Configure Databricks CLI

```bash
# Set your profile name
export DATABRICKS_CONFIG_PROFILE=my-databricks-profile

# Login (this will open a browser)
databricks auth login --profile "$DATABRICKS_CONFIG_PROFILE"

# Verify authentication
databricks current-user me
```

## Step 3: Local Testing (Optional but Recommended)

Test the server locally before deploying:

```bash
# Navigate to project directory
cd /path/to/slack-mcp-server-databricks

# Install dependencies
uv sync

# The .env file is already configured with tokens, so you can run directly:

# Test stdio mode (for Claude Desktop)
uv run slack-mcp-server

# Or test Databricks Apps mode (FastAPI)
uv run slack-mcp-server-databricks
```

**Note:** The Python application will automatically load environment variables from the `.env` file.

Open your browser to `http://localhost:8000` to see the landing page.
The MCP endpoint is at `http://localhost:8000/mcp/`

## Step 4: Build the Wheel Package

```bash
# Build the Python wheel
uv build --wheel
```

This creates:
- `dist/slack_mcp_server_databricks-0.1.0-py3-none-any.whl` - The wheel package
- `.build/` directory with deployment artifacts
  - `slack_mcp_server_databricks-0.1.0-py3-none-any.whl` - Copy of the wheel
  - `requirements.txt` - Points to the wheel file
  - `app.yaml` - App configuration

## Step 5: Deploy to Databricks Apps

### Method A: Using Databricks Bundle (Recommended)

```bash
# Validate the bundle configuration
databricks bundle validate

# Deploy the bundle
databricks bundle deploy

# Check deployment status
databricks apps list
```

### Method B: Using Databricks Apps CLI

```bash
# Get your username
DATABRICKS_USERNAME=$(databricks current-user me | jq -r .userName)

# Create the app
databricks apps create slack-mcp-server-databricks

# Sync files to workspace
databricks sync . "/Users/$DATABRICKS_USERNAME/slack-mcp-server-databricks"

# Deploy the app
databricks apps deploy slack-mcp-server-databricks \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/slack-mcp-server-databricks"
```

## Step 6: Configure Environment Variables

After deployment, you need to set the Slack credentials as environment variables in your Databricks App.

### Using Databricks UI:

1. Go to your Databricks workspace
2. Navigate to "Apps" in the left sidebar
3. Find and click on `slack-mcp-server-databricks`
4. Click "Settings" or "Environment Variables"
5. Add the following variables (from the `.env` file):
   - `SLACK_MCP_XOXC_TOKEN`: `xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34`
   - `SLACK_MCP_XOXD_TOKEN`: `xoxd-PeFvxXXjFH0Q7YieBDxiePYueb%2FoLwit1Ddrh4Dhgd5ClDl9ZcHmPDiwryc12dSa3SNIXIvYNvrHBs3wwP1gLYhkxuL%2BcmOW%2Bamabd%2FnJ7Hfs51EsmDeLU3TgXWteurlnrP1TJXt7qn3N1JBnbmADgvMmkgq8J2Yo0ZMKCQW7C4WWGxbXQ33LwTIkYSAjnlwNJfyjdRUjTnnGqIRfFz2Ip%2FHh70A`
6. Save and restart the app

### Using Databricks CLI:

```bash
# Set environment variables via CLI (using tokens from .env file)
databricks apps update slack-mcp-server-databricks \
  --env SLACK_MCP_XOXC_TOKEN="xoxc-9745578846547-9749919698358-9748524459781-cc6676cf0bddbda3a570e098823682c3c87e66ccab19804af65185c8456a0c34" \
  --env SLACK_MCP_XOXD_TOKEN="xoxd-PeFvxXXjFH0Q7YieBDxiePYueb%2FoLwit1Ddrh4Dhgd5ClDl9ZcHmPDiwryc12dSa3SNIXIvYNvrHBs3wwP1gLYhkxuL%2BcmOW%2Bamabd%2FnJ7Hfs51EsmDeLU3TgXWteurlnrP1TJXt7qn3N1JBnbmADgvMmkgq8J2Yo0ZMKCQW7C4WWGxbXQ33LwTIkYSAjnlwNJfyjdRUjTnnGqIRfFz2Ip%2FHh70A"
```

## Step 7: Access Your Deployed App

Once deployed and configured, your app will be accessible at:

```
https://<your-workspace>.cloud.databricks.com/apps/<app-id>/
```

To find the exact URL:

```bash
# List apps and get the URL
databricks apps list | grep slack-mcp-server-databricks

# Or get detailed info
databricks apps get slack-mcp-server-databricks
```

The MCP endpoint will be at:
```
https://<your-workspace>.cloud.databricks.com/apps/<app-id>/mcp/
```

**Important:** The MCP endpoint URL must end with `/mcp/` (including the trailing slash).

## Step 8: Connect to the MCP Server

### From Python Client:

```python
from databricks.sdk import WorkspaceClient
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession
import asyncio

# Initialize Databricks client
client = WorkspaceClient()

async def main():
    # Your app's MCP endpoint URL
    app_url = "https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/"
    
    # Connect to the MCP server
    async with connect(app_url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool(
                "conversations_history",
                {
                    "channel_id": "#general",
                    "limit": "10"
                }
            )
            print(result)

# Run the async function
asyncio.run(main())
```

### From Claude Desktop:

Edit your Claude Desktop configuration:
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Add:
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

Restart Claude Desktop.

## Verification

Test that everything works:

1. **Check the landing page**: Visit your app URL in a browser
2. **Test MCP endpoint**: Use the Python client example above
3. **Check logs**: In Databricks UI, go to your app and check the logs for any errors

## Updating the App

To update after making changes:

```bash
# Make your changes, then rebuild
uv build --wheel

# Redeploy
databricks bundle deploy

# Or using apps CLI
databricks apps deploy slack-mcp-server-databricks \
  --source-code-path "/Workspace/Users/$DATABRICKS_USERNAME/slack-mcp-server-databricks"
```

## Troubleshooting

### App fails to start

1. Check logs in Databricks UI
2. Verify environment variables are set correctly
3. Check that the wheel file was built successfully

### Authentication errors

1. Verify your Slack tokens are correct and not expired
2. Check that both xoxc and xoxd are set (if using browser tokens)
3. Try with xoxp token instead

### MCP connection fails

1. Verify the URL ends with `/mcp/`
2. Check that the app is running (not stopped or failed)
3. Verify you have network access to the Databricks workspace

### Import errors

1. Rebuild with `uv build --wheel`
2. Check that all dependencies are in pyproject.toml
3. Verify the .build directory was created correctly

## Security Best Practices

1. **Never commit tokens**: Keep tokens in environment variables or secrets
2. **Use Databricks Secrets**: Store tokens in Databricks secrets instead of environment variables
3. **Limit permissions**: Use the minimum required Slack permissions
4. **Monitor usage**: Check app logs regularly for suspicious activity
5. **Rotate tokens**: Regularly rotate your Slack tokens

## Additional Configuration

### Enable message posting:

Set the `SLACK_MCP_ADD_MESSAGE_TOOL` environment variable:

```bash
# Enable for all channels
databricks apps update slack-mcp-server-databricks \
  --env SLACK_MCP_ADD_MESSAGE_TOOL="true"

# Enable for specific channels only
databricks apps update slack-mcp-server-databricks \
  --env SLACK_MCP_ADD_MESSAGE_TOOL="C1234567890,C0987654321"
```

### Configure auto-mark as read:

```bash
databricks apps update slack-mcp-server-databricks \
  --env SLACK_MCP_ADD_MESSAGE_MARK="true"
```

### Enable link unfurling:

```bash
databricks apps update slack-mcp-server-databricks \
  --env SLACK_MCP_ADD_MESSAGE_UNFURLING="true"
```

## Support

For issues or questions:
- Check the [GitHub Issues](https://github.com/murtihash94/slack-mcp-server-databricks/issues)
- Review the [Databricks Apps documentation](https://docs.databricks.com/en/apps/index.html)
- Consult the [MCP documentation](https://modelcontextprotocol.io)

## Next Steps

Now that your Slack MCP Server is deployed on Databricks:

1. Test all the available tools (conversations_history, channels_list, etc.)
2. Integrate it with your LLM applications
3. Set up monitoring and alerts
4. Configure additional Slack workspaces if needed
5. Explore advanced features like message posting and search

Happy building! 🚀
