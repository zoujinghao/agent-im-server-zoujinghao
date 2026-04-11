import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Callable
from ..models.models import Message
from ..tools.tool_registry import ToolRegistry


class AgentEngine:
    def __init__(self, tool_registry: ToolRegistry, max_iterations: int = 10, tool_timeout: int = 30):
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.tool_timeout = tool_timeout  # Timeout in seconds for each tool call

    async def process_conversation(
        self,
        messages: List[Message],
        send_event: Callable[[str, Any], None]
    ) -> tuple[str, list]:
        """
        Process a conversation with the agent engine.
        Returns tuple of (final response text, tool call records)
        """
        conversation_history = self._messages_to_llm_format(messages)
        current_messages = conversation_history.copy()
        all_tool_calls = []
        
        for iteration in range(self.max_iterations):
            # Call LLM (mock implementation)
            llm_response = await self._mock_llm_call(current_messages)
            
            if llm_response.get("type") == "text":
                # Pure text response - we're done
                final_text = llm_response["content"]
                send_event("text_delta", {"content": final_text})
                send_event("done", {"content": final_text})
                return final_text, all_tool_calls
                
            elif llm_response.get("type") == "tool_call":
                # Tool call response - execute tools in parallel
                tool_calls = llm_response.get("tool_calls", [])
                tool_results = []
                
                # Execute all tools concurrently with timeout
                tasks = []
                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    arguments = tool_call["arguments"]
                    
                    # Send tool_call event
                    send_event("tool_call", {
                        "tool_name": tool_name,
                        "arguments": arguments
                    })
                    
                    # Create task for tool execution
                    task = self._execute_tool_with_timeout(tool_name, arguments, send_event)
                    tasks.append((tool_name, arguments, task))
                
                # Wait for all tools to complete (with individual timeouts handled in _execute_tool_with_timeout)
                results = await asyncio.gather(*[task for _, _, task in tasks], return_exceptions=True)
                
                # Process results
                for i, result in enumerate(results):
                    tool_name, arguments = tasks[i][0], tasks[i][1]
                    
                    if isinstance(result, Exception):
                        error_result = f"Error executing {tool_name}: {str(result)}"
                        duration_ms = 0
                    else:
                        error_result = result["result"]
                        duration_ms = result["duration_ms"]
                    
                    # Send tool_result event
                    send_event("tool_result", {
                        "tool_name": tool_name,
                        "result": error_result,
                        "duration_ms": duration_ms
                    })
                    
                    tool_results.append({
                        "tool_name": tool_name,
                        "result": error_result,
                        "duration_ms": duration_ms
                    })
                    
                    # Store tool call info for database saving
                    all_tool_calls.append({
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": error_result,
                        "duration_ms": duration_ms
                    })
                
                # Add tool results to conversation history
                current_messages.append({
                    "role": "assistant",
                    "tool_calls": tool_calls
                })
                
                for result in tool_results:
                    current_messages.append({
                        "role": "tool",
                        "name": result["tool_name"],
                        "content": result["result"]
                    })
            
            else:
                # Unexpected response type
                error_msg = "Unexpected LLM response format"
                send_event("text_delta", {"content": error_msg})
                send_event("done", {"content": error_msg})
                return error_msg, all_tool_calls
        
        # Max iterations reached
        max_iter_msg = "Maximum number of iterations reached. Please try again with a more specific query."
        send_event("text_delta", {"content": max_iter_msg})
        send_event("done", {"content": max_iter_msg})
        return max_iter_msg, all_tool_calls

    def _messages_to_llm_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """Convert our Message objects to LLM-compatible format"""
        llm_messages = []
        for msg in messages:
            if msg.sender_type == "user":
                llm_messages.append({
                    "role": "user",
                    "content": msg.content
                })
            elif msg.sender_type == "agent":
                # Check if this message has tool calls
                if msg.tool_calls:
                    # This is a complex message with tool calls
                    llm_messages.append({
                        "role": "assistant",
                        "content": msg.content if msg.content else None,
                        "tool_calls": msg.tool_calls
                    })
                else:
                    # Simple text message
                    llm_messages.append({
                        "role": "assistant",
                        "content": msg.content
                    })
        return llm_messages

    async def _mock_llm_call(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Mock LLM call that simulates different response types.
        In a real implementation, this would call an actual LLM API.
        """
        await asyncio.sleep(0.1)  # Simulate network delay
        
        last_message = messages[-1] if messages else None
        
        # Simple logic to determine response type
        if last_message and last_message.get("role") == "user":
            content = last_message.get("content", "").lower()
            
            # Check if user is asking for weather
            if "weather" in content or "temperature" in content:
                city = "New York"  # Default city
                # Try to extract city from content
                words = content.split()
                for word in words:
                    if word not in ["what", "is", "the", "weather", "in", "temperature", "like"]:
                        city = word.capitalize()
                        break
                
                return {
                    "type": "tool_call",
                    "tool_calls": [{
                        "name": "get_weather",
                        "arguments": {"city": city}
                    }]
                }
            
            # Check if user is asking for knowledge search
            elif "search" in content or "find" in content or "know" in content:
                query = content.replace("search", "").replace("find", "").replace("know", "").strip()
                if not query:
                    query = "general information"
                
                return {
                    "type": "tool_call",
                    "tool_calls": [{
                        "name": "search_knowledge",
                        "arguments": {"query": query}
                    }]
                }
            
            # Check if user wants to create a task
            elif "task" in content or "create" in content:
                title = "Sample task"
                assignee = "John Doe"
                
                return {
                    "type": "tool_call",
                    "tool_calls": [{
                        "name": "create_task",
                        "arguments": {"title": title, "assignee": assignee}
                    }]
                }
            
            # Default: return simple text response
            else:
                return {
                    "type": "text",
                    "content": f"I understand you said: '{last_message.get('content', '')}'. How can I help you further?"
                }
        
        # If last message was from assistant (tool call), return text response
        elif last_message and last_message.get("role") == "assistant":
            return {
                "type": "text",
                "content": "I've completed the requested action. Is there anything else I can help you with?"
            }
        
        # Default fallback
        return {
            "type": "text",
            "content": "Hello! I'm your AI assistant. How can I help you today?"
        }

    async def _execute_tool_with_timeout(self, tool_name: str, arguments: Dict[str, Any], send_event: Callable) -> Dict[str, Any]:
        """Execute a tool with timeout protection"""
        start_time = time.time()
        try:
            # Apply timeout to tool execution
            result = await asyncio.wait_for(
                self._execute_tool_internal(tool_name, arguments),
                timeout=self.tool_timeout
            )
            duration_ms = int((time.time() - start_time) * 1000)
            return {"result": result, "duration_ms": duration_ms}
            
        except asyncio.TimeoutError:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Tool '{tool_name}' execution timed out after {self.tool_timeout} seconds"
            return {"result": error_msg, "duration_ms": duration_ms}
            
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            error_msg = f"Error executing {tool_name}: {str(e)}"
            return {"result": error_msg, "duration_ms": duration_ms}

    async def _execute_tool_internal(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Internal tool execution without timeout"""
        tool = self.tool_registry.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        # Validate arguments against schema (simplified)
        required_args = tool.json_schema.get("required", [])
        for arg in required_args:
            if arg not in arguments:
                raise ValueError(f"Missing required argument: {arg}")
        
        # Execute the tool function
        if asyncio.iscoroutinefunction(tool.function):
            result = await tool.function(**arguments)
        else:
            result = tool.function(**arguments)
        
        return str(result)