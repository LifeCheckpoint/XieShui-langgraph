from langchain_core.tools import tool
from pathlib import Path

@tool("get_current_working_directory")
def get_current_working_directory() -> str:
    """
    当你需要知道当前的工作目录时，使用此工具。
    它会返回一个字符串，表示当前 Python 脚本执行的工作目录的绝对路径。

    Example:
    - get_current_working_directory: {}
    """
    return f"当前工作目录是: {Path.cwd()}"