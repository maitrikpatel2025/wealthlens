"""
Analytics sub-agent.
Dispatches computation requests to the appropriate tool functions.
"""

from core.tools import TOOL_FUNCTIONS


async def analytics_agent(tool_name: str, args: dict, state: dict) -> dict:
    """
    Execute an analytics tool by name.
    Dispatches to the registered tool function.
    """
    fn = TOOL_FUNCTIONS.get(tool_name)
    if not fn:
        return {"error": f"Unknown tool: {tool_name}"}

    try:
        result = fn(args, state)
        return result
    except Exception as e:
        return {"error": f"Tool '{tool_name}' failed: {str(e)}"}
