"""File operations tool - read, write, move, delete files."""

import os
import shutil
from pathlib import Path
from .base import BaseTool, ToolExecutionError
from .registry import register_tool


@register_tool
class FileOperationsTool(BaseTool):
    """Execute file system operations."""
    
    name = "file_ops"
    description = "Read, write, move, copy, or delete files and folders"
    
    def run(self, operation: str, path: str, content: str = None, destination: str = None) -> dict:
        """
        Execute file operations.
        
        Args:
            operation: 'read', 'write', 'move', 'copy', 'delete', 'list'
            path: File or folder path
            content: Content for write operations
            destination: Destination path for move/copy
        
        Returns:
            Dict with result or error
        """
        try:
            path = os.path.expanduser(path)
            
            if operation == "read":
                with open(path, 'r') as f:
                    return {"content": f.read(), "path": path}
            
            elif operation == "write":
                if content is None:
                    raise ToolExecutionError("Content required for write operation")
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'w') as f:
                    f.write(content)
                return {"status": "written", "path": path}
            
            elif operation == "move":
                if destination is None:
                    raise ToolExecutionError("Destination required for move operation")
                destination = os.path.expanduser(destination)
                shutil.move(path, destination)
                return {"status": "moved", "from": path, "to": destination}
            
            elif operation == "copy":
                if destination is None:
                    raise ToolExecutionError("Destination required for copy operation")
                destination = os.path.expanduser(destination)
                if os.path.isdir(path):
                    shutil.copytree(path, destination)
                else:
                    shutil.copy2(path, destination)
                return {"status": "copied", "from": path, "to": destination}
            
            elif operation == "delete":
                if os.path.isdir(path):
                    shutil.rmtree(path)
                else:
                    os.remove(path)
                return {"status": "deleted", "path": path}
            
            elif operation == "list":
                if os.path.isdir(path):
                    items = os.listdir(path)
                    return {"items": items, "count": len(items), "path": path}
                else:
                    raise ToolExecutionError(f"{path} is not a directory")
            
            else:
                raise ToolExecutionError(f"Unknown operation: {operation}")
        
        except Exception as e:
            raise ToolExecutionError(f"File operation failed: {str(e)}")
