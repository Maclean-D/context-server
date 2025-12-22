import os
import requests
from datetime import datetime, timedelta
import logging
import time
from zoneinfo import ZoneInfo
from .config import config, TZ

logger = logging.getLogger(__name__)

class LimitlessAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.limitless.ai"
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key
        })

    def get_lifelogs(self, start_date: datetime, end_date: datetime = None, timezone: str = None) -> list:
        """Fetch lifelogs for the given date range."""
        if not end_date:
            end_date = start_date + timedelta(days=1)
        
        all_lifelogs = []
        cursor = None
        batch_size = 10  # Much larger batch size
        max_retries = 3
        retry_delay = 1  # seconds
        
        params = {
            "date": start_date.strftime("%Y-%m-%d"),
            "timezone": timezone or str(TZ),
            "includeMarkdown": "true",
            "includeHeadings": "true",  # Try to get section headings
            "direction": "asc",
            "limit": batch_size
        }

        while True:
            if cursor:
                params["cursor"] = cursor

            retries = 0
            while retries < max_retries:
                try:
                    response = self.session.get(f"{self.base_url}/v1/lifelogs", params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    lifelogs = data.get("data", {}).get("lifelogs", [])
                    all_lifelogs.extend(lifelogs)
                    
                    # Get the next cursor from the response
                    next_cursor = data.get("meta", {}).get("lifelogs", {}).get("nextCursor")
                    
                    # If there's no next cursor or we got fewer results than requested, we're done
                    if not next_cursor or len(lifelogs) < batch_size:
                        return all_lifelogs
                        
                    logger.debug(f"Fetched {len(lifelogs)} lifelogs, next cursor: {next_cursor}")
                    cursor = next_cursor
                    break  # Success, exit retry loop
                    
                except (requests.exceptions.Timeout, requests.exceptions.ReadTimeout):
                    retries += 1
                    if retries < max_retries:
                        logger.warning(f"Request timed out, retrying in {retry_delay} seconds... (attempt {retries}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                    logger.error("Max retries reached, moving on to next batch")
                    return all_lifelogs
                except Exception as e:
                    logger.error(f"Error fetching lifelogs: {e}")
                    return all_lifelogs

        return all_lifelogs

def get_conversation_timestamp(conversation: dict) -> str:
    """
    Extract timestamp from a conversation object, handling multiple field variations.
    
    Checks for timestamp in multiple possible fields:
    - timestamp
    - time
    - recorded_at
    - recordedAt
    - metadata.timestamp
    - startTime
    - start_time
    - createdAt
    - created_at
    
    Returns formatted timestamp string or empty string if not found.
    """
    timestamp_fields = [
        "timestamp",
        "time", 
        "recorded_at",
        "recordedAt",
        "startTime",
        "start_time",
        "createdAt",
        "created_at"
    ]
    
    # Check direct fields
    for field in timestamp_fields:
        if conversation.get(field):
            try:
                dt = datetime.fromisoformat(conversation[field])
                return dt.strftime("(%m/%d/%y %I:%M %p)")
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse timestamp from field '{field}': {e}")
                continue
    
    # Check metadata.timestamp
    if conversation.get("metadata") and isinstance(conversation["metadata"], dict):
        if conversation["metadata"].get("timestamp"):
            try:
                dt = datetime.fromisoformat(conversation["metadata"]["timestamp"])
                return dt.strftime("(%m/%d/%y %I:%M %p)")
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse timestamp from metadata.timestamp: {e}")
    
    return ""

def format_lifelog_markdown(lifelog: dict) -> str:
    """Convert a lifelog entry to our markdown format."""
    content = []
    
    # Add title as first heading if present
    if lifelog.get("title"):
        content.append(f"# {lifelog['title']}\n")
    
    # If we have raw markdown, use it directly as it's already in the correct format
    if lifelog.get("markdown"):
        content.append(lifelog["markdown"])
        return "\n".join(content)
    
    # Otherwise format from contents
    if lifelog.get("contents"):
        current_section = None
        section_messages = []
        
        for node in lifelog["contents"]:
            # Handle section headings (heading2)
            if node["type"] == "heading2":
                # If we have a previous section, add it to content
                if current_section and section_messages:
                    content.append(f"## {current_section}\n")
                    content.extend(section_messages)
                    content.append("")  # Add blank line between sections
                
                current_section = node["content"]
                section_messages = []
                continue
            
            # Handle messages/blockquotes
            if node["type"] == "blockquote":
                speaker = node.get("speakerName", "Speaker")
                timestamp = get_conversation_timestamp(node)
                
                message = f"- {speaker} {timestamp}: {node['content']}"
                if current_section:
                    section_messages.append(message)
                else:
                    content.append(message)
            
            # Handle other content types (if any)
            elif node["type"] not in ("heading1", "heading2"):
                content.append(node["content"])
        
        # Add the last section if we have one
        if current_section and section_messages:
            content.append(f"## {current_section}\n")
            content.extend(section_messages)
    
    return "\n\n".join(content)

def format_content_node(node: dict, level: int = 1) -> list:
    """Format a content node into markdown lines."""
    lines = []
    
    if node["type"].startswith("heading"):
        heading_level = int(node["type"][-1])
        lines.append(f"{'#' * heading_level} {node['content']}")
    elif node["type"] == "blockquote":
        speaker = node.get("speakerName", "Speaker")
        timestamp = get_conversation_timestamp(node)
        
        lines.append(f"- {speaker} {timestamp}: {node['content']}")
    else:
        lines.append(node["content"])
    
    if node.get("children"):
        for child in node["children"]:
            lines.extend(format_content_node(child, level + 1))
    
    return lines

def get_last_fetched_date():
    """Find the most recent date that was fetched from the API."""
    last_date = None
    try:
        for root, dirs, files in os.walk(config["docs_dir"]):
            for file in files:
                if file.endswith(".md"):
                    try:
                        date_str = file.split(".")[0]  # Get YYYY-MM-DD from filename
                        file_date = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=TZ)
                        if not last_date or file_date > last_date:
                            # Check if file has content
                            file_path = os.path.join(root, file)
                            if os.path.getsize(file_path) > 0:
                                last_date = file_date
                    except ValueError:
                        continue
    except Exception as e:
        logger.error(f"Error finding last fetched date: {e}")
    
    return last_date

def sync_lifelogs(api_key: str = None, force_start_date: datetime = None):
    """Sync lifelogs to local markdown files."""
    if not api_key and not config.get("limitless_api_key"):
        logger.warning("No Limitless API key configured")
        return
    
    api = LimitlessAPI(api_key or config["limitless_api_key"])
    
    # Determine start date
    if force_start_date:
        start_date = force_start_date
    else:
        last_fetched = get_last_fetched_date()
        if last_fetched:
            start_date = last_fetched  # Start from last fetched date to get any updates
            logger.info(f"Starting sync from last fetched date: {start_date.strftime('%Y-%m-%d')}")
        else:
            # If no files exist, start from February 9th, 2025
            start_date = datetime(2025, 2, 9, tzinfo=TZ)
            logger.info("No existing files found, starting sync from February 9th, 2025")
    
    end_date = datetime.now(TZ) + timedelta(days=1)  # Include today
    
    current_date = start_date
    while current_date < end_date:
        year_dir = os.path.join(config["docs_dir"], str(current_date.year))
        month_dir = os.path.join(year_dir, current_date.strftime("%B"))  # Full month name
        os.makedirs(month_dir, exist_ok=True)
        
        file_path = os.path.join(month_dir, f"{current_date.strftime('%Y-%m-%d')}.md")
        
        logger.info(f"Fetching lifelogs for {current_date.strftime('%Y-%m-%d')}")
        logs = api.get_lifelogs(current_date)
        
        # Debug logging: Show structure of conversations returned from API
        if logs:
            logger.debug(f"Received {len(logs)} conversations from API")
            for idx, log in enumerate(logs):
                logger.debug(f"Conversation {idx + 1} available fields: {list(log.keys())}")
                # Log specific timestamp-related fields if present
                timestamp_info = []
                for field in ["timestamp", "time", "recorded_at", "recordedAt", "startTime", "start_time", "createdAt", "created_at"]:
                    if field in log:
                        timestamp_info.append(f"{field}={log[field]}")
                if log.get("metadata") and isinstance(log["metadata"], dict):
                    if "timestamp" in log["metadata"]:
                        timestamp_info.append(f"metadata.timestamp={log['metadata']['timestamp']}")
                if timestamp_info:
                    logger.debug(f"Conversation {idx + 1} timestamp fields: {', '.join(timestamp_info)}")
        
        if logs:
            content = []
            for log in logs:
                content.append(format_lifelog_markdown(log))
            
            if content:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("\n\n".join(content))
                    logger.info(f"Created/Updated {file_path} with {len(logs)} entries")
                except Exception as e:
                    logger.error(f"Error writing {file_path}: {e}")
        else:
            logger.debug(f"No entries found for {current_date.strftime('%Y-%m-%d')}")
        
        current_date += timedelta(days=1)