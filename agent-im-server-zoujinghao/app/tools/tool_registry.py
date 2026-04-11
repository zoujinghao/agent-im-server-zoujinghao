import json
from typing import Dict, Callable, Any, List
from dataclasses import dataclass


@dataclass
class Tool:
    name: str
    description: str
    json_schema: dict
    function: Callable


class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_builtin_tools()

    def register_tool(self, name: str, description: str, json_schema: dict, function: Callable):
        """Register a new tool"""
        self.tools[name] = Tool(name=name, description=description, json_schema=json_schema, function=function)

    def get_tool(self, name: str) -> Tool:
        """Get a tool by name"""
        return self.tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools with their schemas"""
        tools_info = []
        for tool in self.tools.values():
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.json_schema
            })
        return tools_info

    def _register_builtin_tools(self):
        """Register built-in tools"""
        # Weather tool
        weather_schema = {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "The city name to get weather for"
                }
            },
            "required": ["city"]
        }
        self.register_tool("get_weather", "Get current weather information for a city", weather_schema, self._get_weather)

        # Knowledge search tool
        knowledge_schema = {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query to look up in knowledge base"
                }
            },
            "required": ["query"]
        }
        self.register_tool("search_knowledge", "Search for information in the knowledge base", knowledge_schema, self._search_knowledge)

        # Task creation tool
        task_schema = {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "The title of the task"
                },
                "assignee": {
                    "type": "string",
                    "description": "The person assigned to the task"
                }
            },
            "required": ["title", "assignee"]
        }
        self.register_tool("create_task", "Create a new task with title and assignee", task_schema, self._create_task)

    def _get_weather(self, city: str) -> str:
        """Mock weather function"""
        return f"Current weather in {city}: 22°C, sunny"

    def _search_knowledge(self, query: str) -> str:
        """Mock knowledge search function"""
        return f"Found relevant information about '{query}': This is a mock response from the knowledge base."

    def _create_task(self, title: str, assignee: str) -> str:
        """Mock task creation function"""
        return f"Task '{title}' has been created and assigned to {assignee}."