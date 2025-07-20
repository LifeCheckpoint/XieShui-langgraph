from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from collections import deque
import json

from src.main_agent.utils.knowledge_core.node_edge import Knowledge_Node, Knowledge_Edge

# 知识图谱定义
class Knowledge_Graph(BaseModel):
    """
    定义知识图谱的整体结构，包含所有节点和边。
    """
    nodes: Dict[str, Knowledge_Node] = Field(default={}) # 以 ID 为键存储所有节点
    edges: Dict[str, Knowledge_Edge] = Field(default={}) # 以 ID 为键存储所有边

    def add_node(self, node: Knowledge_Node):
        """
        向图谱中添加一个节点。
        如果节点ID已存在，则抛出ValueError。
        """
        if node.id in self.nodes:
            raise ValueError(f"节点 ID {node.id} 已存在")
        self.nodes[node.id] = node

    def add_edge(self, edge: Knowledge_Edge):
        """
        向图谱中添加一条边。
        检查起始和结束节点是否存在，并更新相关节点的 in_edge/out_edge 列表。
        如果边 ID 已存在或节点不存在，则抛出 ValueError。
        """
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
        start_node_obj.out_edge.append(edge.id) # 更新起始节点的出边列表
        end_node_obj.in_edge.append(edge.id)   # 更新结束节点的入边列表

    def remove_node(self, node_id: str):
        """
        从图谱中移除一个节点及其所有关联的边。
        """
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        
        # 收集所有需要删除的边ID
        edges_to_remove = set(node.in_edge + node.out_edge)

        # 遍历并删除这些边
        for edge_id in list(edges_to_remove): # 复制一份，因为迭代时会修改原列表
            self.remove_edge(edge_id) # 调用 remove_edge 来处理反向链接

        del self.nodes[node_id]

    def remove_edge(self, edge_id: str):
        """
        从图谱中移除一条边，并更新相关节点的in_edge/out_edge列表。
        """
        if edge_id not in self.edges:
            raise ValueError(f'边 ID {edge_id} 不存在')
            
        edge = self.edges[edge_id]
        
        # 从起始节点的出边列表中移除该边ID
        start_node = self.nodes.get(edge.start_node_id)
        if start_node and edge.id in start_node.out_edge:
            start_node.out_edge.remove(edge.id)
        
        # 从结束节点的入边列表中移除该边ID
        end_node = self.nodes.get(edge.end_node_id)
        if end_node and edge.id in end_node.in_edge:
            end_node.in_edge.remove(edge.id)
            
        del self.edges[edge_id]

    class Config:
        """Pydantic 配置，允许模型中包含非BaseModel类型的属性。"""
        arbitrary_types_allowed = True

    # 工具方法

    def get_node(self, node_id: str) -> Optional[Knowledge_Node]:
        """根据ID获取节点对象。"""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> Optional[Knowledge_Edge]:
        """根据ID获取边对象。"""
        return self.edges.get(edge_id)

    def get_all_node(self) -> List[Knowledge_Node]:
        """获取图谱中所有节点。"""
        return list(self.nodes.values())

    def get_all_edge(self) -> List[Knowledge_Edge]:
        """获取图谱中所有边。"""
        return list(self.edges.values())

    def get_out_edge(self, node_id: str) -> List[Knowledge_Edge]:
        """获取指定节点的所有出边对象。"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        return [self.edges[id] for id in node.out_edge]

    def get_in_edge(self, node_id: str) -> List[Knowledge_Edge]:
        """获取指定节点的所有入边对象。"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        return [self.edges[id] for id in node.in_edge]

    def get_neighbours(self, node_id: str) -> List[Knowledge_Node]:
        """获取指定节点的所有邻居节点（包括入边和出边连接的节点）。"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        node_ids = set()
        for edge_id in node.in_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.start_node_id) # 入边的起始节点是邻居
        for edge_id in node.out_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.end_node_id)   # 出边的结束节点是邻居

        node_ids.discard(node.id) # 移除自身
        return [self.nodes[nid] for nid in node_ids]

    def get_out_neighbours(self,node_id:str) -> List[Knowledge_Node]:
        """获取指定节点的所有出方向邻居节点。"""
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        node = self.nodes[node_id]
        node_ids = set()
        for edge_id in node.out_edge:
            edge = self.edges[edge_id]
            node_ids.add(edge.end_node_id) # 只添加出边的目标节点
        return [self.nodes[nid] for nid in node_ids]
    
    def find_path(self, start_node_id: str, goal_node_id: str) -> List[str]:
        """
        使用广度优先搜索（BFS）查找从起始节点到目标节点的最短路径（按节点数量）。
        返回节点ID列表，如果不存在路径则返回空列表。
        """
        if start_node_id not in self.nodes or goal_node_id not in self.nodes:
            raise ValueError("起始或终止节点不存在")
        
        if start_node_id == goal_node_id:
            return [start_node_id]
        
        queue = deque()
        queue.append(start_node_id)
        parent = {start_node_id: None} # 存储每个节点的前驱，用于重建路径
        
        while queue:
            current_id = queue.popleft()
            
            if current_id == goal_node_id:
                path = []
                while current_id is not None:
                    path.append(current_id)
                    current_id = parent[current_id]
                return path[::-1] # 反转路径，使其从起始节点到目标节点
            
            # 获取出邻居的ID
            neighbors = [edge.end_node_id for edge in self.get_out_edge(current_id)]
            
            for neighbor_id in neighbors:
                if neighbor_id not in parent: # 避免重复访问和循环
                    parent[neighbor_id] = current_id
                    queue.append(neighbor_id)
        
        return [] # 未找到路径

    def save_to_file(self, filepath: str):
        """
        将当前知识图谱保存到JSON文件。
        使用 Pydantic 的 model_dump_json 进行序列化。
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.model_dump_json(indent=4))
        print(f"知识图谱已保存到 {filepath}")

    @classmethod
    def load_from_file(cls, filepath: str):
        """
        从 JSON 文件加载知识图谱。
        重建节点、边以及它们之间的内部引用和连接列表。
        """
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        graph = cls()

        # 1. 加载所有节点
        for node_id, node_data in data.get('nodes', {}).items():
            node = Knowledge_Node(**node_data)
            graph.nodes[node.id] = node
        
        # 2. 加载所有边，并重新建立节点引用和节点的in_edge/out_edge列表
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
            # 注意：在 add_edge 方法中已经处理了这些，但 load_from_file 是直接构建，需要手动填充
            # 实际上，如果 load_from_file 内部调用 add_edge，则这些行可以省略
            # 但为了避免 add_edge 的重复检查，这里直接填充更高效
            graph.nodes[edge.start_node_id].out_edge.append(edge.id)
            graph.nodes[edge.end_node_id].in_edge.append(edge.id)

        return graph

