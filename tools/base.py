"""Base definitions for tools."""

class ToolExecutionError(Exception):
    """Raised when a tool fails to execute properly."""


class BaseTool:
    """
    Base interface for tools.

    Attributes:
        name: Human-readable tool name.
        description: Short description of tool behavior.
    """

    name: str
    description: str

    def run(self, **kwargs) -> dict:
        """
        Execute the tool.

        Args:
            **kwargs: Tool-specific parameters.

        Returns:
            A dictionary with tool results.

        Raises:
            ToolExecutionError: When execution fails.
            NotImplementedError: If not implemented by subclasses.
        """
        raise NotImplementedError("Tool must implement run()")

