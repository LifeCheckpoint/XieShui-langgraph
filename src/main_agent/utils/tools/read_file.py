from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_community.document_loaders import UnstructuredFileLoader
from pathlib import Path
from typing import List, Dict, Any

class ReadFileSchema(BaseModel):
    """
    当你需要读取指定路径的文件内容时，使用此工具。
    它会使用 UnstructuredFileLoader 加载文件，并返回一个文档对象列表。

    Example:
    - path: ./data/example.txt
    """
    path: str = Field(description="需要读取的文件的路径。")

@tool("read_file", args_schema=ReadFileSchema)
def read_file(path: str) -> List[Dict[str, Any]]:
    """
    读取指定路径的文件，并将其内容加载为 LangChain 的 Document 对象列表。
    """
    try:
        p = Path(path)
        if not p.is_file():
            return [{"error": f"路径 '{path}' 不是一个有效的文件。"}]
        
        # 使用 UnstructuredFileLoader 加载文件
        loader = UnstructuredFileLoader(str(p))
        documents = loader.load()
        
        # 将 Document 对象序列化为字典列表
        return [doc.model_dump() for doc in documents]
        
    except Exception as e:
        return [{"error": f"读取文件时发生错误: {e}"}]