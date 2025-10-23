"""
Example: Using the Slack MCP Server from Python
================================================

This example shows how to connect to the deployed Slack MCP Server
on Databricks Apps and use its various tools.
"""

import asyncio
from mcp.client.streamable_http import streamablehttp_client as connect
from mcp import ClientSession


# Your Databricks app URL
APP_URL = "https://<workspace>.cloud.databricks.com/apps/<app-id>/mcp/"


async def list_available_tools(session):
    """List all available tools."""
    print("\n=== Available Tools ===")
    tools_result = await session.list_tools()
    for tool in tools_result.tools:
        print(f"- {tool.name}: {tool.description}")
    return tools_result.tools


async def list_resources(session):
    """List all available resources."""
    print("\n=== Available Resources ===")
    resources_result = await session.list_resources()
    for resource in resources_result.resources:
        print(f"- {resource.uri}: {resource.name}")
    return resources_result.resources


async def get_channel_history(session, channel_name="#general", limit="10"):
    """Get recent messages from a channel."""
    print(f"\n=== Channel History: {channel_name} ===")
    result = await session.call_tool(
        "conversations_history",
        {
            "channel_id": channel_name,
            "limit": limit,
            "include_activity_messages": False
        }
    )
    print(result.content[0].text)
    return result


async def list_channels(session, limit=10):
    """List workspace channels."""
    print(f"\n=== Listing Channels (limit={limit}) ===")
    result = await session.call_tool(
        "channels_list",
        {
            "channel_types": "public_channel,private_channel",
            "limit": limit,
            "sort": "popularity"
        }
    )
    print(result.content[0].text)
    return result


async def search_messages(session, query="meeting"):
    """Search for messages."""
    print(f"\n=== Searching Messages: '{query}' ===")
    result = await session.call_tool(
        "conversations_search_messages",
        {
            "search_query": query,
            "limit": 5
        }
    )
    print(result.content[0].text)
    return result


async def get_thread_replies(session, channel_id, thread_ts):
    """Get replies in a thread."""
    print(f"\n=== Thread Replies: {thread_ts} ===")
    result = await session.call_tool(
        "conversations_replies",
        {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "limit": "10"
        }
    )
    print(result.content[0].text)
    return result


async def get_channels_resource(session):
    """Get the channels resource as CSV."""
    print("\n=== Channels Resource (CSV) ===")
    result = await session.read_resource("slack://workspace/channels")
    print(result.contents[0].text[:500] + "..." if len(result.contents[0].text) > 500 else result.contents[0].text)
    return result


async def get_users_resource(session):
    """Get the users resource as CSV."""
    print("\n=== Users Resource (CSV) ===")
    result = await session.read_resource("slack://workspace/users")
    print(result.contents[0].text[:500] + "..." if len(result.contents[0].text) > 500 else result.contents[0].text)
    return result


async def post_message(session, channel_id="#test", text="Hello from MCP!"):
    """
    Post a message to a channel.
    Note: This requires SLACK_MCP_ADD_MESSAGE_TOOL to be enabled.
    """
    print(f"\n=== Posting Message to {channel_id} ===")
    try:
        result = await session.call_tool(
            "conversations_add_message",
            {
                "channel_id": channel_id,
                "payload": text,
                "content_type": "text/markdown"
            }
        )
        print(result.content[0].text)
        return result
    except Exception as e:
        print(f"Error: {e}")
        print("Note: Message posting may be disabled. Set SLACK_MCP_ADD_MESSAGE_TOOL to enable.")


async def main():
    """Main example function."""
    print(f"Connecting to Slack MCP Server at: {APP_URL}")
    
    async with connect(APP_URL) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the session
            print("Initializing MCP session...")
            await session.initialize()
            print("✓ Connected successfully!")
            
            # List available tools and resources
            await list_available_tools(session)
            await list_resources(session)
            
            # Example 1: List channels
            await list_channels(session, limit=5)
            
            # Example 2: Get channel history
            await get_channel_history(session, "#general", limit="5")
            
            # Example 3: Search messages
            await search_messages(session, "project")
            
            # Example 4: Get channels resource
            await get_channels_resource(session)
            
            # Example 5: Get users resource
            await get_users_resource(session)
            
            # Example 6: Post a message (requires tool to be enabled)
            # await post_message(session, "#test", "Hello from Python MCP Client!")
            
            # Example 7: Get thread replies (replace with actual values)
            # await get_thread_replies(session, "C1234567890", "1234567890.123456")
            
            print("\n✓ All examples completed successfully!")


if __name__ == "__main__":
    # Update APP_URL above with your actual Databricks app URL
    # Then run: python example_usage.py
    asyncio.run(main())
