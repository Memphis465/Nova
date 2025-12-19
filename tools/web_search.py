"""Web search and browsing tool."""

import os
import requests
from .base import BaseTool, ToolExecutionError
from .registry import register_tool


@register_tool
class WebSearchTool(BaseTool):
    """Search the web and fetch content."""
    
    name = "web_search"
    description = "Search the web using DuckDuckGo or fetch webpage content"
    
    def run(self, operation: str, query: str = None, url: str = None) -> dict:
        """
        Web operations.
        
        Args:
            operation: 'search' or 'fetch'
            query: Search query for 'search' operation
            url: URL to fetch for 'fetch' operation
        
        Returns:
            Dict with results
        """
        try:
            if operation == "search":
                if query is None:
                    raise ToolExecutionError("Query required for search")
                
                # Use DuckDuckGo instant answers API
                response = requests.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": 1,
                        "skip_disambig": 1
                    },
                    timeout=10
                )
                
                data = response.json()
                
                # Get results
                results = {
                    "abstract": data.get("Abstract", ""),
                    "abstract_url": data.get("AbstractURL", ""),
                    "answer": data.get("Answer", ""),
                    "related": [{"text": r.get("Text"), "url": r.get("FirstURL")} 
                               for r in data.get("RelatedTopics", [])[:5]]
                }
                
                return results
            
            elif operation == "fetch":
                if url is None:
                    raise ToolExecutionError("URL required for fetch")
                
                response = requests.get(url, timeout=10, headers={
                    "User-Agent": "Mozilla/5.0 (compatible; GodmanAI/1.0)"
                })
                
                return {
                    "status_code": response.status_code,
                    "content": response.text[:10000],  # First 10k chars
                    "url": url
                }
            
            else:
                raise ToolExecutionError(f"Unknown operation: {operation}")
        
        except Exception as e:
            raise ToolExecutionError(f"Web operation failed: {str(e)}")
