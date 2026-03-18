"""
Tools module for the Research Assistant.
Provides search and LLM capabilities via Tavily and OpenRouter.
"""

from typing import List, Dict, Any, Optional
import json
from tavily import TavilyClient
from openai import OpenAI
from config import TAVILY_API_KEY, OPENROUTER_API_KEY, validate_config


class SearchTool:
    """Tool for performing web searches using Tavily."""
    
    def __init__(self):
        validate_config()
        self.client = TavilyClient(api_key=TAVILY_API_KEY)
    
    def search(self, query: str, max_results: int = 5, search_depth: str = "basic") -> List[Dict[str, Any]]:
        """
        Perform a web search using Tavily.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return (default: 5)
            search_depth: Search depth - "basic" or "advanced" (default: "basic")
        
        Returns:
            List of search results, each containing:
            - title: Article title
            - url: Source URL
            - content: Article content/snippet
            - score: Relevance score
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth
            )
            
            results = []
            for result in response.get('results', []):
                results.append({
                    'title': result.get('title', ''),
                    'url': result.get('url', ''),
                    'content': result.get('content', ''),
                    'score': result.get('score', 0.0)
                })
            
            return results
        except Exception as e:
            print(f"Error performing search: {e}")
            return []


class LLMTool:
    """Tool for interacting with LLMs via OpenRouter."""
    
    def __init__(self, model: str = "openai/gpt-4o-mini"):
        """
        Initialize the LLM tool.
        
        Args:
            model: Model identifier for OpenRouter (default: "openai/gpt-4o-mini")
        """
        validate_config()
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY
        )
        self.model = model
    
    def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate (None for model default)
        
        Returns:
            Generated text response
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error generating LLM response: {e}")
            return f"Error: {str(e)}"
    
    def generate_with_tools(
        self,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_choice: str = "auto",
        temperature: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate a response with tool calling support.
        
        Args:
            messages: List of message dictionaries
            tools: List of tool definitions (OpenAI function calling format)
            tool_choice: Tool choice mode ("auto", "none", or specific tool)
            temperature: Sampling temperature
        
        Returns:
            Dictionary with 'content' and 'tool_calls' (if any)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
                temperature=temperature
            )
            
            message = response.choices[0].message
            result = {
                'content': message.content or '',
                'tool_calls': []
            }
            
            if message.tool_calls:
                for tool_call in message.tool_calls:
                    result['tool_calls'].append({
                        'id': tool_call.id,
                        'function': {
                            'name': tool_call.function.name,
                            'arguments': json.loads(tool_call.function.arguments)
                        }
                    })
            
            return result
        except Exception as e:
            print(f"Error generating LLM response with tools: {e}")
            return {'content': f"Error: {str(e)}", 'tool_calls': []}
