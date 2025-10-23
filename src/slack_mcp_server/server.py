"""Slack MCP Server implementation."""

import os
import sys
import traceback
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import csv
from io import StringIO
from datetime import datetime, timedelta
import re
from urllib.parse import urlparse, parse_qs
from pathlib import Path

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP, Context
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)


@dataclass
class Message:
    """Slack message data structure."""
    msg_id: str
    user_id: str
    user_name: str
    real_name: str
    channel: str
    thread_ts: str
    text: str
    time: str
    reactions: str
    cursor: str


@dataclass
class Channel:
    """Slack channel data structure."""
    id: str
    name: str
    topic: str
    purpose: str
    member_count: int


@dataclass
class User:
    """Slack user data structure."""
    user_id: str
    user_name: str
    real_name: str


class SlackMCPServer:
    """Slack MCP Server implementation."""

    def __init__(self):
        """Initialize the Slack MCP Server."""
        # Get tokens from environment
        self.xoxc_token = os.getenv("SLACK_MCP_XOXC_TOKEN", "")
        self.xoxd_token = os.getenv("SLACK_MCP_XOXD_TOKEN", "")
        self.xoxp_token = os.getenv("SLACK_MCP_XOXP_TOKEN", "")
        
        # Determine which token to use
        if self.xoxp_token:
            token = self.xoxp_token
        elif self.xoxc_token and self.xoxd_token:
            # For xoxc/xoxd, we'll use xoxc as the token
            token = self.xoxc_token
        else:
            token = ""
        
        self.client = WebClient(token=token) if token else None
        
        # Cache for users and channels
        self.users_cache: Dict[str, User] = {}
        self.channels_cache: Dict[str, Channel] = {}
        self.workspace_info: Optional[Dict[str, Any]] = None
        
        # Check if add_message tool is enabled
        self.add_message_enabled = os.getenv("SLACK_MCP_ADD_MESSAGE_TOOL", "")
        self.add_message_mark = os.getenv("SLACK_MCP_ADD_MESSAGE_MARK", "")
        self.add_message_unfurling = os.getenv("SLACK_MCP_ADD_MESSAGE_UNFURLING", "")
    
    async def initialize(self, ctx: Context):
        """Initialize and authenticate with Slack."""
        if not self.client:
            await ctx.error("No Slack token provided. Set SLACK_MCP_XOXP_TOKEN or both SLACK_MCP_XOXC_TOKEN and SLACK_MCP_XOXD_TOKEN")
            raise ValueError("No Slack token configured")
        
        try:
            # Authenticate
            auth_result = self.client.auth_test()
            self.workspace_info = auth_result.data
            await ctx.info(f"Authenticated with Slack workspace: {auth_result.data.get('team', 'Unknown')}")
            
            # Load caches
            await self._load_users_cache(ctx)
            await self._load_channels_cache(ctx)
            
        except SlackApiError as e:
            await ctx.error(f"Failed to authenticate with Slack: {e.response['error']}")
            raise
    
    async def _load_users_cache(self, ctx: Context):
        """Load users into cache."""
        try:
            await ctx.info("Loading users cache...")
            result = self.client.users_list()
            
            for user in result.data.get("members", []):
                if not user.get("deleted", False):
                    user_obj = User(
                        user_id=user["id"],
                        user_name=user.get("name", ""),
                        real_name=user.get("real_name", "") or user.get("profile", {}).get("real_name", "")
                    )
                    self.users_cache[user["id"]] = user_obj
            
            await ctx.info(f"Loaded {len(self.users_cache)} users")
        except SlackApiError as e:
            await ctx.error(f"Failed to load users: {e.response['error']}")
    
    async def _load_channels_cache(self, ctx: Context):
        """Load channels into cache."""
        try:
            await ctx.info("Loading channels cache...")
            
            # Get all channel types
            channel_types = ["public_channel", "private_channel", "mpim", "im"]
            
            for channel_type in channel_types:
                if channel_type == "im":
                    result = self.client.conversations_list(types="im", limit=1000)
                elif channel_type == "mpim":
                    result = self.client.conversations_list(types="mpim", limit=1000)
                else:
                    types = "public_channel" if channel_type == "public_channel" else "private_channel"
                    result = self.client.conversations_list(types=types, limit=1000)
                
                for channel in result.data.get("channels", []):
                    channel_obj = Channel(
                        id=channel["id"],
                        name=channel.get("name", "") or f"@{self._get_user_name(channel.get('user', ''))}",
                        topic=channel.get("topic", {}).get("value", ""),
                        purpose=channel.get("purpose", {}).get("value", ""),
                        member_count=channel.get("num_members", 0) or 1
                    )
                    self.channels_cache[channel["id"]] = channel_obj
            
            await ctx.info(f"Loaded {len(self.channels_cache)} channels")
        except SlackApiError as e:
            await ctx.error(f"Failed to load channels: {e.response['error']}")
    
    def _get_user_name(self, user_id: str) -> str:
        """Get username from user ID."""
        user = self.users_cache.get(user_id)
        return user.user_name if user else user_id
    
    def _get_channel_id(self, channel_ref: str) -> Optional[str]:
        """Resolve channel reference to channel ID."""
        # If it's already an ID
        if channel_ref.startswith(("C", "D", "G")):
            return channel_ref
        
        # If it starts with # or @, look it up
        if channel_ref.startswith("#"):
            name = channel_ref[1:]
            for channel in self.channels_cache.values():
                if channel.name == name:
                    return channel.id
        elif channel_ref.startswith("@"):
            name = channel_ref[1:]
            for channel in self.channels_cache.values():
                if channel.name == f"@{name}" or channel.name == name:
                    return channel.id
        
        return None
    
    def _parse_limit(self, limit: str) -> tuple[int, Optional[str], Optional[str]]:
        """Parse limit parameter into count, oldest, and latest timestamps."""
        # Check if it's a numeric limit
        if limit.isdigit():
            return int(limit), None, None
        
        # Parse time-based limit (e.g., "1d", "7d", "30d")
        match = re.match(r"(\d+)([dwm])", limit)
        if match:
            value = int(match.group(1))
            unit = match.group(2)
            
            now = datetime.now()
            if unit == "d":
                oldest = now - timedelta(days=value)
            elif unit == "w":
                oldest = now - timedelta(weeks=value)
            elif unit == "m":
                oldest = now - timedelta(days=value * 30)
            else:
                return 50, None, None
            
            return 1000, str(oldest.timestamp()), None
        
        return 50, None, None


# Initialize FastMCP server
mcp = FastMCP("Slack MCP Server on Databricks Apps")
slack_server = SlackMCPServer()


@mcp.tool()
async def conversations_history(
    channel_id: str,
    ctx: Context,
    include_activity_messages: bool = False,
    cursor: str = "",
    limit: str = "1d"
) -> str:
    """
    Get messages from a channel or DM by channel_id.
    
    Args:
        channel_id: ID of the channel (Cxxxxxxxxxx) or name starting with #... or @...
        include_activity_messages: Include activity messages like channel_join/leave
        cursor: Cursor for pagination
        limit: Limit of messages (e.g., "50", "1d", "7d", "30d")
        ctx: MCP context for logging
    """
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        # Resolve channel ID
        resolved_channel_id = slack_server._get_channel_id(channel_id)
        if not resolved_channel_id:
            resolved_channel_id = channel_id
        
        await ctx.info(f"Fetching history for channel {resolved_channel_id}")
        
        # Parse limit
        msg_limit, oldest, latest = slack_server._parse_limit(limit)
        
        # Fetch messages
        kwargs = {
            "channel": resolved_channel_id,
            "limit": msg_limit,
        }
        
        if cursor:
            kwargs["cursor"] = cursor
        if oldest:
            kwargs["oldest"] = oldest
        if latest:
            kwargs["latest"] = latest
        
        result = slack_server.client.conversations_history(**kwargs)
        
        # Format messages as CSV
        messages = []
        for msg in result.data.get("messages", []):
            if not include_activity_messages and msg.get("subtype") in ["channel_join", "channel_leave"]:
                continue
            
            user_id = msg.get("user", "")
            user = slack_server.users_cache.get(user_id)
            
            messages.append({
                "msgID": msg.get("ts", ""),
                "userID": user_id,
                "userName": user.user_name if user else "",
                "realName": user.real_name if user else "",
                "channelID": resolved_channel_id,
                "ThreadTs": msg.get("thread_ts", ""),
                "text": msg.get("text", ""),
                "time": datetime.fromtimestamp(float(msg.get("ts", "0"))).isoformat(),
                "reactions": ",".join([r["name"] for r in msg.get("reactions", [])]),
                "cursor": result.data.get("response_metadata", {}).get("next_cursor", "")
            })
        
        # Convert to CSV
        output = StringIO()
        if messages:
            writer = csv.DictWriter(output, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
        
        return output.getvalue()
        
    except SlackApiError as e:
        await ctx.error(f"Slack API error: {e.response['error']}")
        return f"Error: {e.response['error']}"
    except Exception as e:
        await ctx.error(f"Error fetching conversations history: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return f"Error: {str(e)}"


@mcp.tool()
async def conversations_replies(
    channel_id: str,
    thread_ts: str,
    ctx: Context,
    include_activity_messages: bool = False,
    cursor: str = "",
    limit: str = "1d"
) -> str:
    """
    Get a thread of messages posted to a conversation.
    
    Args:
        channel_id: ID of the channel (Cxxxxxxxxxx) or name starting with #... or @...
        thread_ts: Timestamp of the parent message (e.g., "1234567890.123456")
        include_activity_messages: Include activity messages
        cursor: Cursor for pagination
        limit: Limit of messages
        ctx: MCP context for logging
    """
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        # Resolve channel ID
        resolved_channel_id = slack_server._get_channel_id(channel_id)
        if not resolved_channel_id:
            resolved_channel_id = channel_id
        
        await ctx.info(f"Fetching replies for thread {thread_ts} in channel {resolved_channel_id}")
        
        # Parse limit
        msg_limit, oldest, latest = slack_server._parse_limit(limit)
        
        # Fetch replies
        kwargs = {
            "channel": resolved_channel_id,
            "ts": thread_ts,
            "limit": msg_limit,
        }
        
        if cursor:
            kwargs["cursor"] = cursor
        if oldest:
            kwargs["oldest"] = oldest
        if latest:
            kwargs["latest"] = latest
        
        result = slack_server.client.conversations_replies(**kwargs)
        
        # Format messages as CSV
        messages = []
        for msg in result.data.get("messages", []):
            if not include_activity_messages and msg.get("subtype") in ["channel_join", "channel_leave"]:
                continue
            
            user_id = msg.get("user", "")
            user = slack_server.users_cache.get(user_id)
            
            messages.append({
                "msgID": msg.get("ts", ""),
                "userID": user_id,
                "userName": user.user_name if user else "",
                "realName": user.real_name if user else "",
                "channelID": resolved_channel_id,
                "ThreadTs": msg.get("thread_ts", ""),
                "text": msg.get("text", ""),
                "time": datetime.fromtimestamp(float(msg.get("ts", "0"))).isoformat(),
                "reactions": ",".join([r["name"] for r in msg.get("reactions", [])]),
                "cursor": result.data.get("response_metadata", {}).get("next_cursor", "")
            })
        
        # Convert to CSV
        output = StringIO()
        if messages:
            writer = csv.DictWriter(output, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
        
        return output.getvalue()
        
    except SlackApiError as e:
        await ctx.error(f"Slack API error: {e.response['error']}")
        return f"Error: {e.response['error']}"
    except Exception as e:
        await ctx.error(f"Error fetching thread replies: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return f"Error: {str(e)}"


@mcp.tool()
async def conversations_add_message(
    channel_id: str,
    payload: str,
    ctx: Context,
    thread_ts: str = "",
    content_type: str = "text/markdown"
) -> str:
    """
    Add a message to a channel, private channel, or DM.
    
    Note: This tool is disabled by default. Enable it by setting SLACK_MCP_ADD_MESSAGE_TOOL.
    
    Args:
        channel_id: ID of the channel or name starting with #... or @...
        payload: Message text
        thread_ts: Optional thread timestamp to reply to
        content_type: Content type (text/markdown or text/plain)
        ctx: MCP context for logging
    """
    try:
        # Check if tool is enabled
        if not slack_server.add_message_enabled:
            return "Error: Message posting is disabled. Set SLACK_MCP_ADD_MESSAGE_TOOL to enable."
        
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        # Resolve channel ID
        resolved_channel_id = slack_server._get_channel_id(channel_id)
        if not resolved_channel_id:
            resolved_channel_id = channel_id
        
        await ctx.info(f"Posting message to channel {resolved_channel_id}")
        
        # Post message
        kwargs = {
            "channel": resolved_channel_id,
            "text": payload,
        }
        
        if thread_ts:
            kwargs["thread_ts"] = thread_ts
        
        if content_type == "text/markdown":
            kwargs["mrkdwn"] = True
        
        result = slack_server.client.chat_postMessage(**kwargs)
        
        if result.data.get("ok"):
            return f"Message posted successfully. Timestamp: {result.data.get('ts')}"
        else:
            return f"Failed to post message: {result.data.get('error', 'Unknown error')}"
        
    except SlackApiError as e:
        await ctx.error(f"Slack API error: {e.response['error']}")
        return f"Error: {e.response['error']}"
    except Exception as e:
        await ctx.error(f"Error posting message: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return f"Error: {str(e)}"


@mcp.tool()
async def conversations_search_messages(
    ctx: Context,
    search_query: str = "",
    filter_in_channel: str = "",
    filter_in_im_or_mpim: str = "",
    filter_users_with: str = "",
    filter_users_from: str = "",
    filter_date_before: str = "",
    filter_date_after: str = "",
    filter_date_on: str = "",
    filter_date_during: str = "",
    filter_threads_only: bool = False,
    cursor: str = "",
    limit: int = 20
) -> str:
    """
    Search messages in channels, DMs, or threads.
    
    Args:
        search_query: Search query or Slack message URL
        filter_in_channel: Filter by channel ID or name
        filter_in_im_or_mpim: Filter by DM/MPIM ID or name
        filter_users_with: Filter messages with specific user
        filter_users_from: Filter messages from specific user
        filter_date_before: Filter messages before date
        filter_date_after: Filter messages after date
        filter_date_on: Filter messages on specific date
        filter_date_during: Filter messages during period
        filter_threads_only: Only show thread messages
        cursor: Pagination cursor
        limit: Max results (1-100)
        ctx: MCP context for logging
    """
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        # Build search query
        query_parts = []
        if search_query:
            query_parts.append(search_query)
        
        if filter_in_channel:
            channel_id = slack_server._get_channel_id(filter_in_channel)
            if channel_id:
                query_parts.append(f"in:{channel_id}")
        
        if filter_in_im_or_mpim:
            channel_id = slack_server._get_channel_id(filter_in_im_or_mpim)
            if channel_id:
                query_parts.append(f"in:{channel_id}")
        
        if filter_users_from:
            query_parts.append(f"from:{filter_users_from}")
        
        if filter_date_after:
            query_parts.append(f"after:{filter_date_after}")
        
        if filter_date_before:
            query_parts.append(f"before:{filter_date_before}")
        
        if filter_date_on:
            query_parts.append(f"on:{filter_date_on}")
        
        query = " ".join(query_parts)
        
        await ctx.info(f"Searching with query: {query}")
        
        # Search
        result = slack_server.client.search_messages(
            query=query,
            count=limit,
            page=1 if not cursor else int(cursor)
        )
        
        # Format results as CSV
        messages = []
        for match in result.data.get("messages", {}).get("matches", []):
            user_id = match.get("user", "")
            user = slack_server.users_cache.get(user_id)
            
            messages.append({
                "msgID": match.get("ts", ""),
                "userID": user_id,
                "userName": user.user_name if user else "",
                "realName": user.real_name if user else "",
                "channelID": match.get("channel", {}).get("id", ""),
                "ThreadTs": match.get("thread_ts", ""),
                "text": match.get("text", ""),
                "time": datetime.fromtimestamp(float(match.get("ts", "0"))).isoformat() if match.get("ts") else "",
                "reactions": "",
                "cursor": str(result.data.get("messages", {}).get("pagination", {}).get("page", 1) + 1)
            })
        
        # Convert to CSV
        output = StringIO()
        if messages:
            writer = csv.DictWriter(output, fieldnames=messages[0].keys())
            writer.writeheader()
            writer.writerows(messages)
        
        return output.getvalue()
        
    except SlackApiError as e:
        await ctx.error(f"Slack API error: {e.response['error']}")
        return f"Error: {e.response['error']}"
    except Exception as e:
        await ctx.error(f"Error searching messages: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return f"Error: {str(e)}"


@mcp.tool()
async def channels_list(
    channel_types: str,
    ctx: Context,
    sort: str = "",
    limit: int = 100,
    cursor: str = ""
) -> str:
    """
    Get list of channels.
    
    Args:
        channel_types: Comma-separated types: mpim, im, public_channel, private_channel
        sort: Sort by "popularity" (member count)
        limit: Max results (1-1000)
        cursor: Pagination cursor
        ctx: MCP context for logging
    """
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        await ctx.info(f"Listing channels of types: {channel_types}")
        
        # Parse channel types
        types = [t.strip() for t in channel_types.split(",")]
        
        # Get channels from cache
        channels = []
        for channel in slack_server.channels_cache.values():
            # Filter by type (this is simplified - in production you'd track types)
            channels.append({
                "id": channel.id,
                "name": channel.name,
                "topic": channel.topic,
                "purpose": channel.purpose,
                "memberCount": channel.member_count,
                "cursor": ""
            })
        
        # Sort if requested
        if sort == "popularity":
            channels.sort(key=lambda x: x["memberCount"], reverse=True)
        
        # Apply pagination
        start_idx = int(cursor) if cursor else 0
        paginated_channels = channels[start_idx:start_idx + limit]
        
        # Set cursor for next page
        if start_idx + limit < len(channels):
            for ch in paginated_channels:
                ch["cursor"] = str(start_idx + limit)
        
        # Convert to CSV
        output = StringIO()
        if paginated_channels:
            writer = csv.DictWriter(output, fieldnames=paginated_channels[0].keys())
            writer.writeheader()
            writer.writerows(paginated_channels)
        
        return output.getvalue()
        
    except Exception as e:
        await ctx.error(f"Error listing channels: {str(e)}")
        traceback.print_exc(file=sys.stderr)
        return f"Error: {str(e)}"


@mcp.resource("slack://workspace/channels")
async def channels_resource(ctx: Context) -> str:
    """Get directory of all Slack channels as CSV."""
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        channels = []
        for channel in slack_server.channels_cache.values():
            channels.append({
                "id": channel.id,
                "name": channel.name,
                "topic": channel.topic,
                "purpose": channel.purpose,
                "memberCount": channel.member_count
            })
        
        # Convert to CSV
        output = StringIO()
        if channels:
            writer = csv.DictWriter(output, fieldnames=channels[0].keys())
            writer.writeheader()
            writer.writerows(channels)
        
        return output.getvalue()
        
    except Exception as e:
        await ctx.error(f"Error getting channels resource: {str(e)}")
        return f"Error: {str(e)}"


@mcp.resource("slack://workspace/users")
async def users_resource(ctx: Context) -> str:
    """Get directory of all Slack users as CSV."""
    try:
        if not slack_server.client:
            await slack_server.initialize(ctx)
        
        users = []
        for user in slack_server.users_cache.values():
            users.append({
                "userID": user.user_id,
                "userName": user.user_name,
                "realName": user.real_name
            })
        
        # Convert to CSV
        output = StringIO()
        if users:
            writer = csv.DictWriter(output, fieldnames=users[0].keys())
            writer.writeheader()
            writer.writerows(users)
        
        return output.getvalue()
        
    except Exception as e:
        await ctx.error(f"Error getting users resource: {str(e)}")
        return f"Error: {str(e)}"


def main():
    """Run the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
