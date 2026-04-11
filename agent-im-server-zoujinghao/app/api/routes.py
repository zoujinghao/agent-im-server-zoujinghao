from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, Header
from typing import List, Optional
from app.db.database import Database
from app.models.models import Conversation, Message
from app.agent.agent_engine import AgentEngine
from app.tools.tool_registry import ToolRegistry
from app.websocket.connection_manager import ConnectionManager
from app.api.auth import get_current_user
import json


# Initialize dependencies
db = Database()
tool_registry = ToolRegistry()
agent_engine = AgentEngine(tool_registry)
connection_manager = ConnectionManager()

router = APIRouter()


@router.post("/conversations", response_model=dict)
async def create_conversation(
    title: str = "",
    current_user: bool = Depends(get_current_user)
):
    """Create a new conversation"""
    conversation_id = db.create_conversation(title)
    conversation = db.get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=500, detail="Failed to create conversation")
    return {"id": conversation.id, "title": conversation.title}


@router.get("/conversations", response_model=List[dict])
async def list_conversations(current_user: bool = Depends(get_current_user)):
    """List all conversations"""
    conversations = db.get_conversations()
    return [conv.to_dict() for conv in conversations]


@router.get("/conversations/{conversation_id}/messages", response_model=dict)
async def get_messages(
    conversation_id: int,
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[int] = Query(None, description="Cursor for pagination"),
    current_user: bool = Depends(get_current_user)
):
    """Get messages for a conversation with cursor-based pagination"""
    # Verify conversation exists
    conversation = db.get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    messages, next_cursor = db.get_messages(conversation_id, limit, cursor)
    return {
        "messages": [msg.to_dict() for msg in messages],
        "next_cursor": next_cursor
    }


@router.post("/conversations/{conversation_id}/messages", response_model=dict)
async def send_message(
    conversation_id: int, 
    message_data: dict,
    current_user: bool = Depends(get_current_user)
):
    """Send a message and trigger agent reply"""
    # Verify conversation exists
    conversation = db.get_conversation_by_id(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    content = message_data.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="Message content is required")
    
    # Save user message
    user_message_id = db.create_message(conversation_id, "user", content)
    
    # Get conversation history
    messages, _ = db.get_messages(conversation_id)
    
    # Process with agent engine
    async def send_event(event_type: str, data: dict):
        # Broadcast events to WebSocket connections
        event_data = {
            "type": event_type,
            "data": data,
            "conversation_id": conversation_id
        }
        await connection_manager.broadcast_to_conversation(conversation_id, json.dumps(event_data))
    
    try:
        final_response, tool_calls = await agent_engine.process_conversation(messages, send_event)
        
        # Save agent response
        agent_message_id = db.create_message(conversation_id, "agent", final_response)
        
        # Save tool call records
        for tool_call in tool_calls:
            db.create_tool_call_record(
                message_id=agent_message_id,
                tool_name=tool_call["tool_name"],
                arguments=tool_call["arguments"],
                result=tool_call["result"],
                duration_ms=tool_call["duration_ms"]
            )
        
        return {
            "message_id": agent_message_id,
            "content": final_response,
            "sender_type": "agent"
        }
    except Exception as e:
        error_msg = f"Error processing message: {str(e)}"
        # Save error message
        error_message_id = db.create_message(conversation_id, "agent", error_msg)
        raise HTTPException(status_code=500, detail=error_msg)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, conversation_id: int):
    """WebSocket endpoint for real-time message streaming"""
    await connection_manager.connect(websocket, conversation_id)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            # Echo back for testing (optional)
            await connection_manager.send_personal_message(f"Echo: {data}", websocket)
    except Exception:
        connection_manager.disconnect(websocket, conversation_id)