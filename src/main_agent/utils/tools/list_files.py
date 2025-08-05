from pydantic import BaseModel, Field
from langchain_core.tools import tool
import os

class ListFilesSchema(BaseModel):
    """
    当你需要浏览指定目录下的文件和文件夹时，使用此工具。
    它会返回一个列表，其中包含目录中所有内容的名称。

    Example:
    - path: ./data
    """
    path: str = Field(description="需要浏览的目录路径，可以是相对路径或绝对路径。")

@tool("list_files", args_schema=ListFilesSchema)
def list_files(path: str) -> str:
    """
    浏览指定目录下的文件和文件夹。
    """
    try:
        if not os.path.isdir(path):
            return f"错误: 路径 '{path}' 不是一个有效的目录。"
        
        files = os.listdir(path)
        if not files:
            return f"目录 '{path}' 是空的。"
        
        return f"目录 '{path}' 下的文件和文件夹:\n" + "\n".join(files)
    except Exception as e:
        return f"浏览目录时发生错误: {e}"