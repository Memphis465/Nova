"""Code editing and analysis tool."""

import os
import re
from .base import BaseTool, ToolExecutionError
from .registry import register_tool


@register_tool
class CodeOperationsTool(BaseTool):
    """Edit code files intelligently."""
    
    name = "code_ops"
    description = "Edit, analyze, or refactor code files"
    
    def run(self, operation: str, path: str, **kwargs) -> dict:
        """
        Code operations.
        
        Args:
            operation: 'append', 'replace', 'insert', 'analyze'
            path: File path
            **kwargs: Operation-specific args
        
        Returns:
            Dict with result
        """
        try:
            path = os.path.expanduser(path)
            
            if operation == "append":
                content = kwargs.get("content")
                if content is None:
                    raise ToolExecutionError("Content required")
                
                with open(path, 'a') as f:
                    f.write(content)
                return {"status": "appended", "path": path}
            
            elif operation == "replace":
                old_text = kwargs.get("old_text")
                new_text = kwargs.get("new_text")
                if not old_text or new_text is None:
                    raise ToolExecutionError("old_text and new_text required")
                
                with open(path, 'r') as f:
                    content = f.read()
                
                if old_text not in content:
                    raise ToolExecutionError(f"Text not found: {old_text[:50]}")
                
                new_content = content.replace(old_text, new_text)
                
                with open(path, 'w') as f:
                    f.write(new_content)
                
                return {"status": "replaced", "path": path}
            
            elif operation == "insert":
                line_number = kwargs.get("line_number")
                content = kwargs.get("content")
                if line_number is None or content is None:
                    raise ToolExecutionError("line_number and content required")
                
                with open(path, 'r') as f:
                    lines = f.readlines()
                
                lines.insert(line_number, content + "\n")
                
                with open(path, 'w') as f:
                    f.writelines(lines)
                
                return {"status": "inserted", "path": path, "line": line_number}
            
            elif operation == "analyze":
                with open(path, 'r') as f:
                    content = f.read()
                
                lines = content.split('\n')
                
                # Basic analysis
                analysis = {
                    "total_lines": len(lines),
                    "non_empty_lines": len([l for l in lines if l.strip()]),
                    "comment_lines": len([l for l in lines if l.strip().startswith('#')]),
                    "functions": len(re.findall(r'^\s*def\s+\w+', content, re.MULTILINE)),
                    "classes": len(re.findall(r'^\s*class\s+\w+', content, re.MULTILINE)),
                    "imports": len(re.findall(r'^\s*(?:import|from)\s+', content, re.MULTILINE)),
                }
                
                return {"analysis": analysis, "path": path}
            
            else:
                raise ToolExecutionError(f"Unknown operation: {operation}")
        
        except Exception as e:
            raise ToolExecutionError(f"Code operation failed: {str(e)}")
