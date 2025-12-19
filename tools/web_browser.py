"""
Real web browsing - navigate, click, scroll, interact with pages
"""

import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, Any, List, Optional
from .base import BaseTool, ToolExecutionError
from .registry import register_tool


@register_tool
class WebBrowserTool(BaseTool):
    """Full web browsing capabilities - not just search."""
    
    name = "web_browser"
    description = "Actually browse the web - navigate sites, read articles, extract data"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self.current_url = None
        self.page_content = None
    
    def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        Web browsing actions.
        
        Actions:
            - navigate: Go to URL and get full page content
            - extract_links: Get all links from current page
            - extract_text: Get clean text content
            - extract_data: Extract specific data (emails, prices, etc.)
            - search_page: Find text on current page
            - get_article: Get article content (clean, readable)
        """
        try:
            if action == "navigate":
                return self._navigate(kwargs.get("url"))
            
            elif action == "extract_links":
                return self._extract_links()
            
            elif action == "extract_text":
                return self._extract_text(kwargs.get("selector"))
            
            elif action == "extract_data":
                return self._extract_data(kwargs.get("data_type"))
            
            elif action == "search_page":
                return self._search_page(kwargs.get("query"))
            
            elif action == "get_article":
                return self._get_article(kwargs.get("url"))
            
            else:
                raise ToolExecutionError(f"Unknown action: {action}")
        
        except Exception as e:
            raise ToolExecutionError(f"Browser error: {str(e)}")
    
    def _navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL and load page."""
        response = self.session.get(url, timeout=15)
        response.raise_for_status()
        
        self.current_url = url
        self.page_content = response.text
        
        soup = BeautifulSoup(self.page_content, 'html.parser')
        
        # Get page title
        title = soup.find('title')
        title_text = title.get_text() if title else "No title"
        
        # Get meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc.get('content') if meta_desc else ""
        
        # Count elements
        links_count = len(soup.find_all('a'))
        images_count = len(soup.find_all('img'))
        
        return {
            "url": url,
            "title": title_text,
            "description": description,
            "links_count": links_count,
            "images_count": images_count,
            "status": "loaded"
        }
    
    def _extract_links(self) -> Dict[str, Any]:
        """Extract all links from current page."""
        if not self.page_content:
            raise ToolExecutionError("No page loaded. Navigate first.")
        
        soup = BeautifulSoup(self.page_content, 'html.parser')
        links = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text().strip()
            if text and href.startswith('http'):
                links.append({"text": text, "url": href})
        
        return {
            "links": links[:50],  # First 50 links
            "total_count": len(links)
        }
    
    def _extract_text(self, selector: Optional[str] = None) -> Dict[str, Any]:
        """Extract clean text from page."""
        if not self.page_content:
            raise ToolExecutionError("No page loaded.")
        
        soup = BeautifulSoup(self.page_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        if selector:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(separator='\n', strip=True)
            else:
                text = ""
        else:
            text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        clean_text = '\n'.join(lines)
        
        return {
            "text": clean_text[:5000],  # First 5000 chars
            "full_length": len(clean_text)
        }
    
    def _extract_data(self, data_type: str) -> Dict[str, Any]:
        """Extract specific data types from page."""
        if not self.page_content:
            raise ToolExecutionError("No page loaded.")
        
        soup = BeautifulSoup(self.page_content, 'html.parser')
        results = []
        
        if data_type == "emails":
            import re
            text = soup.get_text()
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            results = list(set(emails))[:20]
        
        elif data_type == "prices":
            import re
            text = soup.get_text()
            prices = re.findall(r'\$\d+(?:\.\d{2})?', text)
            results = prices[:20]
        
        elif data_type == "images":
            for img in soup.find_all('img', src=True)[:20]:
                results.append({
                    "src": img['src'],
                    "alt": img.get('alt', '')
                })
        
        return {
            "data_type": data_type,
            "results": results,
            "count": len(results)
        }
    
    def _search_page(self, query: str) -> Dict[str, Any]:
        """Search for text on current page."""
        if not self.page_content:
            raise ToolExecutionError("No page loaded.")
        
        soup = BeautifulSoup(self.page_content, 'html.parser')
        text = soup.get_text().lower()
        query_lower = query.lower()
        
        found = query_lower in text
        count = text.count(query_lower)
        
        return {
            "found": found,
            "count": count,
            "query": query
        }
    
    def _get_article(self, url: str) -> Dict[str, Any]:
        """Get clean article content (works for news sites, blogs)."""
        response = self.session.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find article content
        article = soup.find('article')
        if not article:
            # Try common content containers
            article = soup.find(['main', 'div'], class_=['content', 'post', 'entry'])
        
        if not article:
            article = soup
        
        # Remove unwanted elements
        for element in article(['script', 'style', 'nav', 'footer', 'aside']):
            element.decompose()
        
        # Get title
        title = soup.find('h1')
        title_text = title.get_text().strip() if title else "No title"
        
        # Get text
        text = article.get_text(separator='\n', strip=True)
        lines = [line.strip() for line in text.split('\n') if line.strip() and len(line.strip()) > 20]
        
        return {
            "url": url,
            "title": title_text,
            "content": '\n\n'.join(lines)[:8000],  # First 8000 chars
            "paragraphs": len(lines)
        }
