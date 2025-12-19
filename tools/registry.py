"""Registry helpers for tools."""

TOOL_REGISTRY = {}


def register_tool(tool_cls):
    """
    Register a tool class by its name attribute.
    """
    TOOL_REGISTRY[tool_cls.name] = tool_cls


def get_tool(name: str):
    """
    Retrieve a tool class by name.
    """
    return TOOL_REGISTRY.get(name)


def list_tools():
    """
    List registered tool names.
    """
    return list(TOOL_REGISTRY.keys())

