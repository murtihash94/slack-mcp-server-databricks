"""FastAPI app for Databricks Apps deployment."""

from pathlib import Path
from slack_mcp_server.server import mcp
from fastapi import FastAPI
from fastapi.responses import FileResponse

STATIC_DIR = Path(__file__).parent / "static"

# Create the streamable HTTP app from the MCP server
mcp_app = mcp.streamable_http_app()

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Slack MCP Server",
    description="Slack MCP Server on Databricks Apps",
    lifespan=lambda _: mcp.session_manager.run(),
)


@app.get("/", include_in_schema=False)
async def serve_index():
    """Serve the landing page."""
    return FileResponse(STATIC_DIR / "index.html")


# Mount the MCP app to handle MCP requests
app.mount("/", mcp_app)
