from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.tools import tool

from src.graph_manager.knowledge_core.knowledge_graph_integration import KnowledgeGraphIntegration

# 初始化一个 KnowledgeGraphIntegration 实例，供所有工具函数使用
kgi = KnowledgeGraphIntegration()

class GetAllNodeSchema(BaseModel):
    """获取当前图谱中所有节点的简要信息（ID和标题）。"""
    pass

@tool("get_all_node", args_schema=GetAllNodeSchema)
def get_all_node() -> str:
    """获取当前图谱中所有节点的简要信息（ID和标题）。"""
    return kgi.get_all_node()

class GetAllEdgeSchema(BaseModel):
    """获取当前图谱中所有边的简要信息（ID和标题）。"""
    pass

@tool("get_all_edge", args_schema=GetAllEdgeSchema)
def get_all_edge() -> str:
    """获取当前图谱中所有边的简要信息（ID和标题）。"""
    return kgi.get_all_edge()

class GetNodeInfoSchema(BaseModel):
    """获取当前图谱中指定ID的节点信息。"""
    node_id: str = Field(description="要查询的节点ID。")

@tool("get_node_info", args_schema=GetNodeInfoSchema)
def get_node_info(node_id: str) -> str:
    """获取当前图谱中指定ID的节点信息。"""
    return kgi.get_node_info(node_id)

class FindPathSchema(BaseModel):
    """查找两个节点之间的最短路径。"""
    start_node_id: str = Field(description="起始节点的ID。")
    end_node_id: str = Field(description="结束节点的ID。")
    with_description: bool = Field(default=False, description="是否在结果中包含路径上节点的描述。")
    with_edge_description: bool = Field(default=False, description="是否在结果中包含路径上边的描述。")

@tool("find_path", args_schema=FindPathSchema)
def find_path(start_node_id: str, end_node_id: str, with_description: bool = False, with_edge_description: bool = False) -> str:
    """查找两个节点之间的最短路径。"""
    return kgi.find_path(start_node_id, end_node_id, with_description, with_edge_description)

class SearchNodesByTagSchema(BaseModel):
    """根据一个或多个标签搜索节点。"""
    tags: List[str] = Field(description="要搜索的标签列表。")
    mode: str = Field(default='AND', description="搜索模式，'AND' 表示节点必须包含所有标签，'OR' 表示节点包含任一标签即可。")
    case_sensitive: bool = Field(default=False, description="是否区分大小写。")

@tool("search_nodes_by_tag", args_schema=SearchNodesByTagSchema)
def search_nodes_by_tag(tags: List[str], mode: str = 'AND', case_sensitive: bool = False) -> str:
    """根据一个或多个标签搜索节点。"""
    return kgi.search_nodes_by_tag(tags, mode, case_sensitive)

# 将所有读取工具函数收集到一个列表中
reading_tool_list = [
    get_all_node,
    get_all_edge,
    get_node_info,
    find_path,
    search_nodes_by_tag,
]