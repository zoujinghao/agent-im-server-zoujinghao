import sqlite3
import os
from datetime import datetime
from typing import List, Optional, Tuple
from ..models.models import Conversation, Message, ToolCallRecord


class Database:
    def __init__(self, db_path: str = "agent_im_server.db"):
        self.db_path = db_path
        self.init_database()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def init_database(self):
        """Initialize the database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL,
                sender_type TEXT NOT NULL CHECK(sender_type IN ('user', 'agent')),
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tool_calls TEXT,
                FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
            )
        ''')

        # Create tool_call_records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tool_call_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message_id INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                arguments TEXT NOT NULL,
                result TEXT NOT NULL,
                duration_ms INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE CASCADE
            )
        ''')

        conn.commit()
        conn.close()

    def create_conversation(self, title: str = "") -> int:
        """Create a new conversation and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO conversations (title) VALUES (?)",
            (title or f"Conversation {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}",)
        )
        conversation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return conversation_id

    def get_conversations(self) -> List[Conversation]:
        """Get all conversations"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at FROM conversations ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        
        conversations = []
        for row in rows:
            conversations.append(Conversation(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2].replace(' ', 'T'))
            ))
        return conversations

    def create_message(self, conversation_id: int, sender_type: str, content: str, tool_calls: list = None) -> int:
        """Create a new message and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        cursor.execute(
            "INSERT INTO messages (conversation_id, sender_type, content, tool_calls) VALUES (?, ?, ?, ?)",
            (conversation_id, sender_type, content, tool_calls_json)
        )
        message_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return message_id

    def get_messages(self, conversation_id: int, limit: int = 50, cursor_id: int = None) -> Tuple[List[Message], int]:
        """Get messages for a conversation with cursor-based pagination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if cursor_id:
            cursor.execute(
                """SELECT id, conversation_id, sender_type, content, created_at, tool_calls 
                   FROM messages 
                   WHERE conversation_id = ? AND id < ? 
                   ORDER BY id DESC LIMIT ?""",
                (conversation_id, cursor_id, limit)
            )
        else:
            cursor.execute(
                """SELECT id, conversation_id, sender_type, content, created_at, tool_calls 
                   FROM messages 
                   WHERE conversation_id = ? 
                   ORDER BY id DESC LIMIT ?""",
                (conversation_id, limit)
            )
        
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        next_cursor = None
        
        for i, row in enumerate(rows):
            tool_calls = json.loads(row[5]) if row[5] else []
            messages.append(Message(
                id=row[0],
                conversation_id=row[1],
                sender_type=row[2],
                content=row[3],
                created_at=datetime.fromisoformat(row[4].replace(' ', 'T')),
                tool_calls=tool_calls
            ))
            
            if i == len(rows) - 1:
                next_cursor = row[0]
        
        # Reverse to get chronological order
        messages.reverse()
        
        return messages, next_cursor

    def create_tool_call_record(self, message_id: int, tool_name: str, arguments: dict, result: str, duration_ms: int) -> int:
        """Create a tool call record"""
        conn = self.get_connection()
        cursor = conn.cursor()
        arguments_json = json.dumps(arguments)
        cursor.execute(
            "INSERT INTO tool_call_records (message_id, tool_name, arguments, result, duration_ms) VALUES (?, ?, ?, ?, ?)",
            (message_id, tool_name, arguments_json, result, duration_ms)
        )
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id

    def get_conversation_by_id(self, conversation_id: int) -> Optional[Conversation]:
        """Get a conversation by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, created_at FROM conversations WHERE id = ?", (conversation_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Conversation(
                id=row[0],
                title=row[1],
                created_at=datetime.fromisoformat(row[2].replace(' ', 'T'))
            )
        return None