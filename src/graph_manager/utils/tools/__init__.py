from langgraph.prebuilt import ToolNode

from src.graph_manager.utils.tools.attempt_completion import attempt_completion
from src.graph_manager.utils.tools.klgraph_abort import klgraph_abort
from src.graph_manager.utils.tools.graph_management import management_tool_list
from src.graph_manager.utils.tools.graph_reading import reading_tool_list
from src.graph_manager.utils.tools.graph_writing import writing_tool_list

# 合并所有工具列表
tool_list = [attempt_completion, klgraph_abort] + management_tool_list + reading_tool_list + writing_tool_list
"""
工具列表，包含了所有可用的工具函数
"""

tools = ToolNode(tool_list)
"""
工具节点，封装了所有工具函数，便于在图中使用
"""

__all__ = ["tool_list", "tools"]