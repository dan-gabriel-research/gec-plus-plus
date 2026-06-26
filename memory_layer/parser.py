# parser.py
# Reads conversation exports from ChatGPT, Claude, or plain text.
# Returns a list of Exchange objects: {role, text, timestamp, source}

import json
import os
from dataclasses import dataclass
from typing import List


@dataclass
class Exchange:
    role: str        # "user" or "assistant"
    text: str        # the message content
    timestamp: float # unix timestamp (0 if unknown)
    source: str      # "chatgpt", "claude", or "text"
    conversation_id: str  # groups messages into conversations


def parse_file(filepath: str) -> List[Exchange]:
    """
    Auto-detects format and returns a flat list of Exchange objects.
    Supported: ChatGPT conversations.json, Claude export JSON, plain .txt
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".txt":
        return _parse_text(filepath)

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    # ChatGPT format: list of conversations, each with "mapping" dict
    if isinstance(data, list) and len(data) > 0:
        if "mapping" in data[0]:
            return _parse_chatgpt(data)
        # Claude format: list of conversations with "chat_messages"
        if "chat_messages" in data[0]:
            return _parse_claude(data)

    raise ValueError(f"Unrecognized export format in {filepath}")


def _parse_chatgpt(data: list) -> List[Exchange]:
    exchanges = []
    for conv in data:
        conv_id = conv.get("id", conv.get("title", "unknown"))
        mapping = conv.get("mapping", {})
        # Sort nodes by create_time
        nodes = sorted(
            [v for v in mapping.values() if v.get("message")],
            key=lambda n: n["message"].get("create_time") or 0
        )
        for node in nodes:
            msg = node["message"]
            role = msg.get("author", {}).get("role", "")
            if role not in ("user", "assistant"):
                continue
            # Content can be a string or a list of parts
            content = msg.get("content", {})
            if isinstance(content, dict):
                parts = content.get("parts", [])
                text = " ".join(str(p) for p in parts if isinstance(p, str))
            else:
                text = str(content)
            text = text.strip()
            if not text:
                continue
            exchanges.append(Exchange(
                role=role,
                text=text,
                timestamp=msg.get("create_time") or 0.0,
                source="chatgpt",
                conversation_id=str(conv_id)
            ))
    return exchanges


def _parse_claude(data: list) -> List[Exchange]:
    exchanges = []
    for conv in data:
        conv_id = conv.get("uuid", conv.get("name", "unknown"))
        for msg in conv.get("chat_messages", []):
            role = msg.get("sender", "")
            if role == "human":
                role = "user"
            elif role == "assistant":
                role = "assistant"
            else:
                continue
            text = msg.get("text", "").strip()
            if not text:
                continue
            exchanges.append(Exchange(
                role=role,
                text=text,
                timestamp=0.0,
                source="claude",
                conversation_id=str(conv_id)
            ))
    return exchanges


def _parse_text(filepath: str) -> List[Exchange]:
    """
    Simple plain text: alternating lines prefixed with 'User:' or 'Assistant:'
    """
    exchanges = []
    conv_id = os.path.basename(filepath)
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.lower().startswith("user:"):
                exchanges.append(Exchange("user", line[5:].strip(), 0.0, "text", conv_id))
            elif line.lower().startswith("assistant:"):
                exchanges.append(Exchange("assistant", line[10:].strip(), 0.0, "text", conv_id))
    return exchanges


def summary(exchanges: List[Exchange]) -> str:
    sources = set(e.source for e in exchanges)
    convs = set(e.conversation_id for e in exchanges)
    user_msgs = sum(1 for e in exchanges if e.role == "user")
    asst_msgs = sum(1 for e in exchanges if e.role == "assistant")
    return (
        f"Parsed {len(exchanges)} messages across {len(convs)} conversations "
        f"({user_msgs} user, {asst_msgs} assistant) — source: {', '.join(sources)}"
    )
