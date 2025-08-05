from pydantic import BaseModel, Field
from langchain_core.tools import tool
import os

class CreateFileSchema(BaseModel):
    """
    当你需要在指定路径创建一个新文件并写入内容时，使用此工具。
    
    重要提示:
    - 在调用此工具之前，你必须先使用 'ask_question' 工具向用户确认他们的意图。
    - 此工具不允许覆盖已存在的文件。如果文件已存在，操作将失败。

    Example:
    - path: ./data/new_file.txt
    - content: 这是新文件的内容。
    """
    path: str = Field(description="要创建的文件的完整路径，包括文件名。")
    content: str = Field(description="要写入新文件的内容。")

@tool("create_file", args_schema=CreateFileSchema)
def create_file(path: str, content: str) -> str:
    """
    安全地创建一个新文件并写入内容。
    """
    try:
        # 检查文件是否已存在
        if os.path.exists(path):
            return f"错误: 文件 '{path}' 已存在。不允许覆盖文件。"
        
        # 创建并写入文件
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return f"文件 '{path}' 已成功创建。"
    except Exception as e:
        return f"创建文件时发生错误: {e}"