from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

# 节点定义
class Knowledge_Node(BaseModel):
    """
    定义知识图谱中的一个节点。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(default="Node")
    description: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list) # 节点标签
    in_edge: List[str] = Field(default_factory=list)  # 入边列表
    out_edge: List[str] = Field(default_factory=list)  # 出边列表

# 边定义
class Knowledge_Edge(BaseModel):
    """
    定义知识图谱中的一条边，连接两个节点。
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(default="Edge")
    start_node_id: str
    end_node_id: str
    description: Optional[str] = Field(default=None)

    # 内部属性，用于在内存中直接引用节点对象，提高访问效率
    # 这些属性在 Pydantic 序列化时默认不会被包含
    _start_node: Optional[Knowledge_Node] = None
    _end_node: Optional[Knowledge_Node] = None

    @property
    def start_node(self) -> Knowledge_Node:
        """获取起始节点对象。"""
        if self._start_node is None:
            raise ValueError("Start node not linked. Load graph first.")
        return self._start_node

    @property
    def end_node(self) -> Knowledge_Node:
        """获取结束节点对象。"""
        if self._end_node is None:
            raise ValueError("End node not linked. Load graph first.")
        return self._end_node

    class Config:
        """Pydantic 配置，控制序列化行为。"""
        arbitrary_types_allowed = True
        json_encoders = {
            Knowledge_Node: lambda v: v.id # 遇到 Knowledge_Node 对象时，只序列化其 id
        }
