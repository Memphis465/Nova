from godman_ai.tools.base import BaseTool, ToolExecutionError


class EchoTool(BaseTool):
    name = "echo"
    description = "Returns the provided text."

    def run(self, text: str, **kwargs) -> dict:
        """
        Return the provided text.

        Args:
            text: Input text to echo back.

        Returns:
            dict containing {"text": text}
        """
        if not isinstance(text, str):
            raise ToolExecutionError("Parameter 'text' must be a string.")
        return {"text": text}

