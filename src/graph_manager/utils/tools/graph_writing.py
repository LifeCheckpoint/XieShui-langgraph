from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List
from langchain_core.tools import tool
import json

from src.graph_manager.utils.kgi_init import kgi

class AddNodeToCurrentGraphSchema(BaseModel):
    """向当前选中的图谱中添加一个新节点。"""
    title: str = Field(description="节点的标题。")
    description: Optional[str] = Field(default=None, description="节点的描述。")
    id: Optional[str] = Field(default=None, description="节点的ID。如果未提供，将自动生成。")
    tags: Optional[List[str]] = Field(default=None, description="节点的标签列表。")

@tool("add_node_to_current_graph", args_schema=AddNodeToCurrentGraphSchema)
def add_node_to_current_graph(title: str, description: Optional[str] = None, id: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """向当前选中的图谱中添加一个新节点。"""
    return kgi.add_node_to_current_graph(title, description, id, tags)


class AddEdgeToCurrentGraphSchema(BaseModel):
    """向当前选中的图谱中添加一条新边。"""
    start_node_id: str = Field(description="起始节点的ID。")
    end_node_id: str = Field(description="结束节点的ID。")
    title: str = Field(description="边的标题，描述了两个节点间的关系。")
    description: Optional[str] = Field(default=None, description="边的详细描述。")
    id: Optional[str] = Field(default=None, description="边的ID。如果未提供，将自动生成。")

@tool("add_edge_to_current_graph", args_schema=AddEdgeToCurrentGraphSchema)
def add_edge_to_current_graph(start_node_id: str, end_node_id: str, title: str, description: Optional[str] = None, id: Optional[str] = None) -> str:
    """向当前选中的图谱中添加一条新边。"""
    return kgi.add_edge_to_current_graph(start_node_id, end_node_id, title, description, id)


class DeleteItemsSchema(BaseModel):
    """通过ID批量删除节点和边。"""
    node_ids: Optional[List[str]] = Field(default=None, description="要删除的节点ID列表。")
    edge_ids: Optional[List[str]] = Field(default=None, description="要删除的边ID列表。")

@tool("delete_items", args_schema=DeleteItemsSchema)
def delete_items(node_ids: Optional[List[str]] = None, edge_ids: Optional[List[str]] = None) -> str:
    """通过ID批量删除节点和边。"""
    return kgi.delete_items(node_ids, edge_ids)


class UpdateNodeInCurrentGraphSchema(BaseModel):
    """更新当前图谱中指定ID的节点信息。"""
    node_id: str = Field(description="要更新的节点ID。")
    title: Optional[str] = Field(default=None, description="新的节点标题。")
    description: Optional[str] = Field(default=None, description="新的节点描述。")
    tags: Optional[List[str]] = Field(default=None, description="新的节点标签列表。")

@tool("update_node_in_current_graph", args_schema=UpdateNodeInCurrentGraphSchema)
def update_node_in_current_graph(node_id: str, title: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
    """更新当前图谱中指定ID的节点信息。"""
    return kgi.update_node_in_current_graph(node_id, title, description, tags)


class UpdateEdgeInCurrentGraphSchema(BaseModel):
    """更新当前图谱中指定ID的边信息。"""
    edge_id: str = Field(description="要更新的边ID。")
    title: Optional[str] = Field(default=None, description="新的边标题。")
    description: Optional[str] = Field(default=None, description="新的边描述。")

@tool("update_edge_in_current_graph", args_schema=UpdateEdgeInCurrentGraphSchema)
def update_edge_in_current_graph(edge_id: str, title: Optional[str] = None, description: Optional[str] = None) -> str:
    """更新当前图谱中指定ID的边信息。"""
    return kgi.update_edge_in_current_graph(edge_id, title, description)


class BatchAddFromJSONSchema(BaseModel):
    """通过JSON数据批量添加节点和边。"""
    json_data: str = Field(description='包含节点和边列表的JSON字符串。格式参见工具文档。')

@tool("batch_add_from_json", args_schema=BatchAddFromJSONSchema)
def batch_add_from_json(json_data: str) -> str:
    """通过JSON数据批量添加节点和边。"""
    return kgi.batch_add_from_json(json_data)


# 将所有写入工具函数收集到一个列表中
writing_tool_list = [
    add_node_to_current_graph,
    add_edge_to_current_graph,
    delete_items,
    update_node_in_current_graph,
    update_edge_in_current_graph,
    batch_add_from_json,
]