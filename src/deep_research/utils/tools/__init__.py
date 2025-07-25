from langgraph.prebuilt import ToolNode

tool_list = []
"""
工具列表，包含了所有可用的工具函数
"""

tools = ToolNode(tool_list)
"""
工具节点，封装了所有工具函数，便于在图中使用
"""

__all__ = ["tool_list", "tools"]