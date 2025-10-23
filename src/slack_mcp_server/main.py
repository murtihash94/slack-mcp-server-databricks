"""Main entry point for local development with uvicorn."""

import uvicorn


def main():
    """Run the server with uvicorn for local development."""
    uvicorn.run(
        "slack_mcp_server.app:app",  # import path to your `app`
        host="0.0.0.0",
        port=8000,
        reload=True,  # optional
    )


if __name__ == "__main__":
    main()
