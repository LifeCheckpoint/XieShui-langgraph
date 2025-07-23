from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.tools import tool

from src.graph_manager.utils.kgi_init import kgi

class SetCurrentGraphSchema(BaseModel):
    """设置当前操作的知识图谱。"""
    name: str = Field(description="要设置为当前图谱的名称。")

@tool("set_current_graph", args_schema=SetCurrentGraphSchema)
def set_current_graph(name: str) -> str:
    """设置当前操作的知识图谱。"""
    return kgi.set_current_graph(name)


class SummarizeGraphContentSchema(BaseModel):
    """为LLM提供当前知识图谱的高层次摘要。"""
    max_nodes: int = Field(default=10, description="摘要中包含的核心节点的最大数量。")
    max_edges: int = Field(default=10, description="摘要中包含的随机边的最大数量。")

@tool("summarize_graph_content", args_schema=SummarizeGraphContentSchema)
def summarize_graph_content(max_nodes: int = 10, max_edges: int = 10) -> str:
    """通过随机采样，为LLM提供当前知识图谱的高层次摘要。"""
    return kgi.summarize_graph_content(max_nodes, max_edges)


class SaveCurrentGraphSchema(BaseModel):
    """保存当前图谱到文件。"""
    pass

@tool("save_current_graph", args_schema=SaveCurrentGraphSchema)
def save_current_graph() -> str:
    """保存当前图谱到文件。"""
    return kgi.save_current_graph()


# 将所有管理工具函数收集到一个列表中
management_tool_list = [
    set_current_graph,
    summarize_graph_content,
    save_current_graph,
]