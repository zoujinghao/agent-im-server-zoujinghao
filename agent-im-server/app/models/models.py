from datetime import datetime
from typing import Optional, List
import sqlite3
import json


class Conversation:
    def __init__(self, id: int = None, title: str = "", created_at: datetime = None):
        self.id = id
        self.title = title
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class Message:
    def __init__(
        self,
        id: int = None,
        conversation_id: int = None,
        sender_type: str = "user",  # "user" or "agent"
        content: str = "",
        created_at: datetime = None,
        tool_calls: List[dict] = None
    ):
        self.id = id
        self.conversation_id = conversation_id
        self.sender_type = sender_type
        self.content = content
        self.created_at = created_at or datetime.utcnow()
        self.tool_calls = tool_calls or []

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_type": self.sender_type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tool_calls": self.tool_calls
        }


class ToolCallRecord:
    def __init__(
        self,
        id: int = None,
        message_id: int = None,
        tool_name: str = "",
        arguments: dict = None,
        result: str = "",
        duration_ms: int = 0,
        created_at: datetime = None
    ):
        self.id = id
        self.message_id = message_id
        self.tool_name = tool_name
        self.arguments = arguments or {}
        self.result = result
        self.duration_ms = duration_ms
        self.created_at = created_at or datetime.utcnow()

    def to_dict(self):
        return {
            "id": self.id,
            "message_id": self.message_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }