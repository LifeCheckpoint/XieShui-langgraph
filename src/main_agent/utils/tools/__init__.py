from langgraph.prebuilt import ToolNode

from src.main_agent.utils.tools.attempt_completion import attempt_completion
from src.main_agent.utils.tools.ask_question import ask_question
from src.main_agent.utils.tools.python_eval import python_eval
from src.main_agent.utils.tools.deep_research import deep_research
from src.main_agent.utils.tools.graph_manager_tool import graph_manager
from src.main_agent.utils.tools.read_file import read_file
from src.main_agent.utils.tools.create_file import create_file
from src.main_agent.utils.tools.list_files import list_files
from src.main_agent.utils.tools.get_cwd import get_current_working_directory

tool_list = [
    attempt_completion, ask_question, python_eval, deep_research, graph_manager,
    read_file, create_file, list_files, get_current_working_directory,
]
"""
工具列表，包含了所有可用的工具函数
"""

tools = ToolNode(tool_list)
"""
工具节点，封装了所有工具函数，便于在图中使用
"""

__all__ = ["tool_list", "tools"]