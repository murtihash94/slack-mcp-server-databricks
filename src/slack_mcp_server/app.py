"""FastAPI app for Databricks Apps deployment."""

import os
from pathlib import Path
from slack_mcp_server.server import mcp, slack_server
from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from pydantic import BaseModel

STATIC_DIR = Path(__file__).parent / "static"
ENV_FILE = Path(__file__).parent.parent.parent / ".env"

# Create the streamable HTTP app from the MCP server
mcp_app = mcp.streamable_http_app()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Slack MCP Server",
    description="Slack MCP Server on Databricks Apps",
    lifespan=lambda _: mcp.session_manager.run(),
)


class TokenUpdate(BaseModel):
    """Token update request model."""
    xoxc_token: str
    xoxd_token: str


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the landing page."""
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/config", include_in_schema=False)
async def serve_config():
    """Serve the token configuration page."""
    return FileResponse(STATIC_DIR / "config.html")


@app.post("/api/update-tokens", include_in_schema=False)
async def update_tokens(xoxc_token: str = Form(...), xoxd_token: str = Form(...)):
    """Update Slack tokens in the .env file and reload configuration."""
    try:
        # Validate tokens
        if not xoxc_token.startswith("xoxc-"):
            raise HTTPException(status_code=400, detail="Invalid xoxc token format")
        if not xoxd_token.startswith("xoxd-"):
            raise HTTPException(status_code=400, detail="Invalid xoxd token format")
        
        # Read current .env file
        env_content = []
        if ENV_FILE.exists():
            with open(ENV_FILE, 'r') as f:
                env_content = f.readlines()
        
        # Update or add tokens
        updated = {
            'SLACK_MCP_XOXC_TOKEN': False,
            'SLACK_MCP_XOXD_TOKEN': False
        }
        
        new_content = []
        for line in env_content:
            if line.startswith('SLACK_MCP_XOXC_TOKEN='):
                new_content.append(f'SLACK_MCP_XOXC_TOKEN="{xoxc_token}"\n')
                updated['SLACK_MCP_XOXC_TOKEN'] = True
            elif line.startswith('SLACK_MCP_XOXD_TOKEN='):
                new_content.append(f'SLACK_MCP_XOXD_TOKEN="{xoxd_token}"\n')
                updated['SLACK_MCP_XOXD_TOKEN'] = True
            else:
                new_content.append(line)
        
        # Add tokens if they weren't in the file
        if not updated['SLACK_MCP_XOXC_TOKEN']:
            new_content.append(f'SLACK_MCP_XOXC_TOKEN="{xoxc_token}"\n')
        if not updated['SLACK_MCP_XOXD_TOKEN']:
            new_content.append(f'SLACK_MCP_XOXD_TOKEN="{xoxd_token}"\n')
        
        # Write updated .env file
        with open(ENV_FILE, 'w') as f:
            f.writelines(new_content)
        
        # Update environment variables
        os.environ['SLACK_MCP_XOXC_TOKEN'] = xoxc_token
        os.environ['SLACK_MCP_XOXD_TOKEN'] = xoxd_token
        
        # Reinitialize the Slack server with new tokens
        slack_server.xoxc_token = xoxc_token
        slack_server.xoxd_token = xoxd_token
        
        # Reinitialize the Slack client
        if xoxc_token and xoxd_token:
            from slack_sdk import WebClient
            slack_server.client = WebClient(token=xoxc_token)
            # Clear caches to force reload
            slack_server.users_cache = {}
            slack_server.channels_cache = {}
            slack_server.workspace_info = None
        
        return RedirectResponse(url="/config?success=true", status_code=303)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update tokens: {str(e)}")


@app.get("/api/current-tokens", include_in_schema=False)
async def get_current_tokens():
    """Get masked current tokens (for display purposes)."""
    xoxc = os.getenv('SLACK_MCP_XOXC_TOKEN', '')
    xoxd = os.getenv('SLACK_MCP_XOXD_TOKEN', '')
    
    # Mask tokens for security (show first 10 and last 4 characters)
    def mask_token(token: str) -> str:
        if len(token) > 20:
            return f"{token[:10]}...{token[-4:]}"
        return "Not set"
    
    return {
        "xoxc_token": mask_token(xoxc),
        "xoxd_token": mask_token(xoxd),
        "xoxc_set": bool(xoxc),
        "xoxd_set": bool(xoxd)
    }


# Mount the MCP app to handle MCP requests
app.mount("/", mcp_app)
