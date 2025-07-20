from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
import json
class Knowledge_Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    title: str = None
    description: Optional[str] = None
    in_edge: List[str] = []
    out_edge: List[str] = []

class Knowledge_Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(default="Edge")
    start_node_id: str
    end_node_id: str
    description: Optional[str] = None

    # 为了保持原有的接口，可以添加属性来获取实际的节点对象
    # 但这些属性在序列化时不会被包含
    _start_node: Optional[Knowledge_Node] = None
    _end_node: Optional[Knowledge_Node] = None

    @property
    def start_node(self) -> Knowledge_Node:
        if self._start_node is None:
            raise ValueError("Start node not linked. Load graph first.")
        return self._start_node

    @property
    def end_node(self) -> Knowledge_Node:
        if self._end_node is None:
            raise ValueError("End node not linked. Load graph first.")
        return self._end_node

    # Pydantic 控制序列化行为
    class Config:
        # 允许在模型中定义非 BaseModel 属性 (_start_node, _end_node)
        arbitrary_types_allowed = True
        # 在序列化时，不包含以下划线开头的私有属性
        json_encoders = {
            Knowledge_Node: lambda v: v.id # 当遇到 Knowledge_Node 对象，只序列化其id
        }


class Knowledge_Graph(BaseModel):
    nodes: Dict[str, Knowledge_Node] = {}
    edges: Dict[str, Knowledge_Edge] = {}

    def add_node(self, node: Knowledge_Node):
        if node.id in self.nodes:
            raise ValueError(f"节点 ID {node.id} 已存在")
        self.nodes[node.id] = node

    def add_edge(self, edge: Knowledge_Edge):
        # 检查节点是否存在
        if edge.start_node_id not in self.nodes:
            raise ValueError(f"起始节点 ID {edge.start_node_id} 不存在")
        if edge.end_node_id not in self.nodes:
            raise ValueError(f"结束节点 ID {edge.end_node_id} 不存在")
        if edge.id in self.edges:
            raise ValueError(f"边 ID {edge.id} 已存在")

        # 获取实际的节点对象并设置到边的内部属性
        start_node_obj = self.nodes[edge.start_node_id]
        end_node_obj = self.nodes[edge.end_node_id]
        edge._start_node = start_node_obj
        edge._end_node = end_node_obj

        self.edges[edge.id] = edge
        start_node_obj.out_edge.append(edge.id)
        end_node_obj.in_edge.append(edge.id)

    def get_node(self, node_id: str):
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str):
        return self.edges.get(edge_id)

    def get_all_node(self):
        return list(self.nodes.values())

    def get_all_edge(self):
        return list(self.edges.values())

    def get_out_edge(self, node_id: str):
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        return [self.edges[id] for id in node.out_edge]

    def get_in_edge(self, node_id: str):
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        return [self.edges[id] for id in node.in_edge]

    def get_neighbours(self, node_id: str):
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        node_ids = set()
        for edge_id in node.in_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.start_node_id)
        for edge_id in node.out_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.end_node_id)

        node_ids.discard(node.id) # 移除自身
        return [self.nodes[nid] for nid in node_ids]

    def get_out_neighbours(self,node_id:str):
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        node_ids = set()
        for edge_id in node.out_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.end_node_id) # 只添加出边的目标节点
        return [self.nodes[nid] for nid in node_ids]
    
    def remove_node(self, node_id: str):
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        
        # 收集所有需要删除的边ID
        edges_to_remove = set(node.in_edge + node.out_edge)

        # 遍历并删除这些边
        for edge_id in list(edges_to_remove): # 复制一份，因为迭代时会修改原列表
            self.remove_edge(edge_id) # 调用remove_edge来处理反向链接

        del self.nodes[node_id]

    def remove_edge(self,edge_id:str):
        if edge_id not in self.edges:
            raise ValueError(f'边 ID {edge_id} 不存在')
            
        edge = self.edges[edge_id]
        
        # 从起始节点的出边列表中移除
        start_node = self.nodes.get(edge.start_node_id)
        if start_node and edge.id in start_node.out_edge:
            start_node.out_edge.remove(edge.id)
        
        # 从结束节点的入边列表中移除
        end_node = self.nodes.get(edge.end_node_id)
        if end_node and edge.id in end_node.in_edge:
            end_node.in_edge.remove(edge.id)
            
        del self.edges[edge_id]

    def find_path(self, start_node_id: str, goal_node_id: str) -> List[str]:
        if start_node_id not in self.nodes or goal_node_id not in self.nodes:
            raise ValueError("起始或终止节点不存在")
        
        if start_node_id == goal_node_id:
            return [start_node_id]
        
        queue = deque()
        queue.append(start_node_id)
        parent = {start_node_id: None}
        
        while queue:
            current_id = queue.popleft()
            
            if current_id == goal_node_id:
                path = []
                while current_id is not None:
                    path.append(current_id)
                    current_id = parent[current_id]
                return path[::-1]
            
            # 获取出邻居的ID
            neighbors = [edge.end_node_id for edge in self.get_out_edge(current_id)]
            
            for neighbor_id in neighbors:
                if neighbor_id not in parent:
                    parent[neighbor_id] = current_id
                    queue.append(neighbor_id)
        
        return []

    def save_to_file(self, filepath: str):
        """将当前知识图谱保存到JSON文件。"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=4))
        print(f"知识图谱已保存到 {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str):
        """从JSON文件加载知识图谱。"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = cls()

        # 加载所有节点
        for node_id, node_data in data.get('nodes', {}).items():
            node = Knowledge_Node(**node_data)
            graph.nodes[node.id] = node
        
        # 加载所有边，并重新建立节点引用
        for edge_id, edge_data in data.get('edges', {}).items():
            # 创建一个临时的字典，不包含 _start_node 和 _end_node，以便 Pydantic 正确解析
            temp_edge_data = {k: v for k, v in edge_data.items() if not k.startswith('_')}
            edge = Knowledge_Edge(**temp_edge_data) # 此时 edge.start_node_id 和 edge.end_node_id 是字符串

            # 重新链接实际的节点对象
            if edge.start_node_id in graph.nodes:
                edge._start_node = graph.nodes[edge.start_node_id]
            else:
                raise ValueError(f"加载边 {edge.id} 时，起始节点 {edge.start_node_id} 不存在")
            
            if edge.end_node_id in graph.nodes:
                edge._end_node = graph.nodes[edge.end_node_id]
            else:
                raise ValueError(f"加载边 {edge.id} 时，结束节点 {edge.end_node_id} 不存在")

            graph.edges[edge.id] = edge
            
            # 重新填充节点的 in_edge 和 out_edge 列表
            graph.nodes[edge.start_node_id].out_edge.append(edge.id)
            graph.nodes[edge.end_node_id].in_edge.append(edge.id)

        return graph

    # Pydantic 控制序列化行为
    class Config:
        arbitrary_types_allowed = True

