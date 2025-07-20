from langgraph.prebuilt import ToolNode

from src.main_agent.utils.tools.attempt_completion import attempt_completion
from src.main_agent.utils.tools.ask_question import ask_question
from src.main_agent.utils.tools.python_eval import python_eval
from src.main_agent.utils.tools.deep_research import deep_research

tool_list = [attempt_completion, ask_question, python_eval, deep_research]
"""
工具列表，包含了所有可用的工具函数
"""

tools = ToolNode(tool_list)
"""
工具节点，封装了所有工具函数，便于在图中使用
"""

__all__ = ["tool_list", "tools"]