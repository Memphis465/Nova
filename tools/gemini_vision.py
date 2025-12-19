"""
Gemini API integration - Vision and video analysis
"""

import os
import requests
import base64
from typing import Dict, Any, Optional
from .base import BaseTool, ToolExecutionError
from .registry import register_tool


@register_tool
class GeminiVisionTool(BaseTool):
    """Analyze images and videos using Google Gemini."""
    
    name = "gemini_vision"
    description = "Analyze images, videos, or ask Gemini Pro questions"
    
    def __init__(self):
        self.api_key = os.environ.get("GEMINI_API_KEY")
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
    
    def run(self, operation: str, **kwargs) -> Dict[str, Any]:
        """
        Operations:
            - analyze_image: Analyze image from URL or file path
            - analyze_video: Analyze video content
            - ask: Ask Gemini Pro a question
            - vision_chat: Multi-turn conversation with vision
        """
        if not self.api_key:
            return {
                "error": "GEMINI_API_KEY not set",
                "setup": "Get key from: https://makersuite.google.com/app/apikey"
            }
        
        try:
            if operation == "analyze_image":
                return self._analyze_image(
                    kwargs.get("image_path"),
                    kwargs.get("image_url"),
                    kwargs.get("prompt", "Describe this image in detail")
                )
            
            elif operation == "analyze_video":
                return self._analyze_video(
                    kwargs.get("video_url"),
                    kwargs.get("prompt", "Describe what happens in this video")
                )
            
            elif operation == "ask":
                return self._ask_gemini(kwargs.get("question"))
            
            else:
                raise ToolExecutionError(f"Unknown operation: {operation}")
        
        except Exception as e:
            raise ToolExecutionError(f"Gemini API error: {str(e)}")
    
    def _analyze_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        prompt: str = "Describe this image"
    ) -> Dict[str, Any]:
        """Analyze image using Gemini Vision."""
        
        # Prepare image data
        if image_path:
            with open(os.path.expanduser(image_path), 'rb') as f:
                image_data = base64.b64encode(f.read()).decode()
            image_source = "file"
        elif image_url:
            response = requests.get(image_url)
            image_data = base64.b64encode(response.content).decode()
            image_source = "url"
        else:
            raise ToolExecutionError("Provide either image_path or image_url")
        
        # Call Gemini API
        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if "error" in result:
            raise ToolExecutionError(f"API error: {result['error']['message']}")
        
        text = result['candidates'][0]['content']['parts'][0]['text']
        
        return {
            "analysis": text,
            "source": image_source,
            "model": "gemini-1.5-flash"
        }
    
    def _analyze_video(self, video_url: str, prompt: str) -> Dict[str, Any]:
        """Analyze video content."""
        
        url = f"{self.base_url}/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [
                    {"text": prompt},
                    {"video_url": {"uri": video_url}}
                ]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=60)
        result = response.json()
        
        if "error" in result:
            raise ToolExecutionError(f"API error: {result['error']['message']}")
        
        text = result['candidates'][0]['content']['parts'][0]['text']
        
        return {
            "analysis": text,
            "video_url": video_url,
            "model": "gemini-1.5-flash"
        }
    
    def _ask_gemini(self, question: str) -> Dict[str, Any]:
        """Ask Gemini Pro a question."""
        
        url = f"{self.base_url}/models/gemini-pro:generateContent?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": question}]
            }]
        }
        
        response = requests.post(url, json=payload, timeout=30)
        result = response.json()
        
        if "error" in result:
            raise ToolExecutionError(f"API error: {result['error']['message']}")
        
        text = result['candidates'][0]['content']['parts'][0]['text']
        
        return {
            "answer": text,
            "model": "gemini-pro"
        }
