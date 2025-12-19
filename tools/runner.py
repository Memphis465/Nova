"""Tool runner that discovers and executes registered tools."""

import time

from .loader import discover_tools
from .registry import get_tool
from .base import ToolExecutionError


class ToolRunner:
    """
    Discovers tools and provides a simple interface to execute them.
    """

    def __init__(self) -> None:
        discover_tools()

    def run(self, tool_name: str, **kwargs) -> dict:
        """
        Execute a tool by name with provided parameters.

        Args:
            tool_name: The registered tool name.
            **kwargs: Parameters forwarded to the tool's run method.

        Returns:
            A result dictionary containing success status, tool name,
            duration, and tool-specific result or error information.

        Raises:
            ToolExecutionError: If the tool is not registered.
        """
        tool_cls = get_tool(tool_name)
        if not tool_cls:
            raise ToolExecutionError(f"Unknown tool: {tool_name}")

        tool = tool_cls()
        start = time.time()
        try:
            result = tool.run(**kwargs)
        except Exception as e:
            return {
                "ok": False,
                "tool": tool_name,
                "error": str(e),
                "trace": type(e).__name__,
            }
        end = time.time()
        return {
            "ok": True,
            "tool": tool_name,
            "duration_ms": int((end - start) * 1000),
            "result": result,
        }

