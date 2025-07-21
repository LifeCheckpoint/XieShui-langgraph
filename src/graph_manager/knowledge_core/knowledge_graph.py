from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
from collections import deque
import networkx as nx
import json

from src.graph_manager.knowledge_core.node_edge import Knowledge_Node, Knowledge_Edge

# 知识图谱定义
class Knowledge_Graph(BaseModel):
    """
    定义知识图谱的整体结构，包含所有节点和边。
    """
    name: str = Field(default="Knowledge Graph") # 图谱名称
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
        
    def update_node(self, node_id: str, title: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None):
        """
        更新一个已存在节点的信息。
        ID 和边列表不能通过此方法修改。
        """
        if node_id not in self.nodes:
            raise ValueError(f"节点 ID {node_id} 不存在")
        
        node = self.nodes[node_id]
        
        if title is not None:
            node.title = title
        if description is not None:
            node.description = description
        if tags is not None:
            node.tags = tags

    def update_edge(self, edge_id: str, title: Optional[str] = None, description: Optional[str] = None):
        """
        更新一个已存在边的信息。
        ID 和连接的节点不能通过此方法修改。
        """
        if edge_id not in self.edges:
            raise ValueError(f"边 ID {edge_id} 不存在")
            
        edge = self.edges[edge_id]
        
        if title is not None:
            edge.title = title
        if description is not None:
            edge.description = description

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
        
        # 创建图谱实例并设置名称
        graph = cls()
        graph.name = data.get('name', 'Knowledge Graph')

        # 1. 加载所有节点，先清空它们的in_edge和out_edge列表
        for node_id, node_data in data.get('nodes', {}).items():
            node = Knowledge_Node(**node_data)
            # 清空边列表，稍后会重新填充
            node.in_edge = []
            node.out_edge = []
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
            graph.nodes[edge.start_node_id].out_edge.append(edge.id)
            graph.nodes[edge.end_node_id].in_edge.append(edge.id)

        return graph
    
    def get_high_in_degree_nodes(self, top_k: int = 10) -> List[Tuple[Knowledge_Node, int]]:
        """
        获取入度最高的节点排名。
        
        Args:
            top_k (int): 返回排名前 k 的节点。
        
        Returns:
            List[Tuple[Knowledge_Node, int]]: 一个元组列表，每个元组包含节点对象和其入度值。
        """
        nodes_with_in_degree = [
            (node, len(node.in_edge)) for node in self.nodes.values()
        ]
        nodes_with_in_degree.sort(key=lambda x: x[1], reverse=True)
        return nodes_with_in_degree[:top_k]
 
    def get_high_out_degree_nodes(self, top_k: int = 10) -> List[Tuple[Knowledge_Node, int]]:
        """
        获取出度最高的节点排名。
        
        Args:
            top_k (int): 返回排名前 k 的节点。
        
        Returns:
            List[Tuple[Knowledge_Node, int]]: 一个元组列表，每个元组包含节点对象和其出度值。
        """
        nodes_with_out_degree = [
            (node, len(node.out_edge)) for node in self.nodes.values()
        ]
        nodes_with_out_degree.sort(key=lambda x: x[1], reverse=True)
        return nodes_with_out_degree[:top_k]
 
    def _to_networkx(self) -> nx.DiGraph:
        """
        内部辅助方法：将当前图转换为 networkx.DiGraph 对象。
        """
        G = nx.DiGraph()
        for node_id in self.nodes:
            G.add_node(node_id)
        for edge in self.edges.values():
            G.add_edge(edge.start_node_id, edge.end_node_id)
        return G
    
    def get_high_betweenness_centrality_nodes(self, top_k: int = 10, approximate: bool = False) -> List[Tuple[Knowledge_Node, float]]:
        """
        获取介数中心性最高的节点排名。
        对于大于几百个节点的图，精确计算可能较慢，可以选择近似计算。
        
        Args:
            top_k (int): 返回排名前 k 的节点。
            approximate (bool): 如果为True，则使用采样进行近似计算，速度更快。
                                对于<1000节点的图，通常不需要。
        
        Returns:
            List[Tuple[Knowledge_Node, float]]: 一个元组列表，每个元组包含节点对象和其介数中心性得分。
        """
        if not self.nodes:
            return []
        G = self._to_networkx()
        
        # 对于<1000节点的稀疏图，精确计算很快。但提供近似选项以备不时之需。
        k_sample = int(len(self.nodes) * 0.2) if approximate else None
        
        centrality = nx.betweenness_centrality(G, k=k_sample, normalized=True)
        
        sorted_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)
        
        result = [
            (self.nodes[node_id], score) for node_id, score in sorted_nodes[:top_k]
        ]
        return result
 
    def get_high_closeness_centrality_nodes(self, top_k: int = 10) -> List[Tuple[Knowledge_Node, float]]:
        """
        获取接近中心性最高的节点排名。
        
        Args:
            top_k (int): 返回排名前 k 的节点。
        
        Returns:
            List[Tuple[Knowledge_Node, float]]: 一个元组列表，每个元组包含节点对象和其接近中心性得分。
        """
        if not self.nodes:
            return []
        G = self._to_networkx()
        centrality = nx.closeness_centrality(G)
        
        sorted_nodes = sorted(centrality.items(), key=lambda item: item[1], reverse=True)
        
        result = [
            (self.nodes[node_id], score) for node_id, score in sorted_nodes[:top_k]
        ]
        return result
 
    def search_nodes_by_keyword(self, keyword: str, case_sensitive: bool = False) -> List[Knowledge_Node]:
        """
        根据关键词搜索节点。关键词会匹配节点的 title、description 和 tags。
        
        Args:
            keyword (str): 要搜索的关键词。
            case_sensitive (bool): 是否区分大小写。默认为False。
        
        Returns:
            List[Knowledge_Node]: 匹配的节点对象列表。
        """
        results = []
        search_term = keyword if case_sensitive else keyword.lower()
        
        for node in self.nodes.values():
            title = node.title if case_sensitive else node.title.lower()
            description = ""
            if node.description:
                description = node.description if case_sensitive else node.description.lower()
            
            tags_content = " ".join(node.tags) if case_sensitive else " ".join(tag.lower() for tag in node.tags)

            if search_term in title or search_term in description or search_term in tags_content:
                results.append(node)
        return results
 
    def search_edges_by_keyword(self, keyword: str, case_sensitive: bool = False) -> List[Knowledge_Edge]:
        """
        根据关键词搜索边。关键词会匹配边的 title 和 description。
        
        Args:
            keyword (str): 要搜索的关键词。
            case_sensitive (bool): 是否区分大小写。默认为False。
        
        Returns:
            List[Knowledge_Edge]: 匹配的边对象列表。
        """
        results = []
        search_term = keyword if case_sensitive else keyword.lower()
        
        for edge in self.edges.values():
            title = edge.title if case_sensitive else edge.title.lower()
            description = ""
            if edge.description:
                description = edge.description if case_sensitive else edge.description.lower()
            
            if search_term in title or search_term in description:
                results.append(edge)
        return results

    def search_nodes_by_tag(self, tags: List[str], mode: str = 'AND', case_sensitive: bool = False) -> List[Knowledge_Node]:
        """
        根据一个或多个标签搜索节点。

        Args:
            tags (List[str]): 要搜索的标签列表。
            mode (str): 搜索模式，'AND' 表示节点必须包含所有标签，'OR' 表示节点包含任一标签即可。默认为 'AND'。
            case_sensitive (bool): 是否区分大小写。默认为False。

        Returns:
            List[Knowledge_Node]: 匹配的节点对象列表。
        """
        if not tags:
            return []

        results = []
        search_tags = set(tags) if case_sensitive else set(tag.lower() for tag in tags)

        for node in self.nodes.values():
            node_tags = set(node.tags) if case_sensitive else set(tag.lower() for tag in node.tags)

            if mode.upper() == 'AND':
                if search_tags.issubset(node_tags):
                    results.append(node)
            elif mode.upper() == 'OR':
                if not search_tags.isdisjoint(node_tags):
                    results.append(node)
        return results
 
    def get_k_hop_neighborhood(self, start_node_id: str, k: int) -> Knowledge_Graph:
        """
        从一个起始节点开始，获取至多 k 次向外扩散得到的子图。
        
        Args:
            start_node_id (str): 起始节点的ID。
            k (int): 扩散的跳数（hops）。k=1 表示直接邻居。
        
        Returns:
            Knowledge_Graph: 一个包含邻域内所有节点和边的新图对象。
        """
        if start_node_id not in self.nodes:
            raise ValueError(f"起始节点 ID {start_node_id} 不存在")
 
        subgraph = Knowledge_Graph(name=f"{self.name}_subgraph")
        
        # 使用BFS进行遍历
        queue = deque([(start_node_id, 0)]) # (node_id, current_depth)
        visited_nodes = {start_node_id}
        
        # 首先将起始节点添加到子图中
        subgraph.add_node(self.nodes[start_node_id].model_copy(deep=True))
 
        while queue:
            current_id, depth = queue.popleft()
            
            if depth >= k:
                continue
            
            # 遍历当前节点的所有出边
            for edge_id in self.nodes[current_id].out_edge:
                edge = self.edges[edge_id]
                neighbor_id = edge.end_node_id
                
                # 如果邻居节点未被访问过，则加入队列和子图
                if neighbor_id not in visited_nodes:
                    visited_nodes.add(neighbor_id)
                    # 复制节点对象，避免修改原图
                    subgraph.add_node(self.nodes[neighbor_id].model_copy(deep=True))
                    queue.append((neighbor_id, depth + 1))
                
                # 只要边在扩散路径上，且两个节点都在子图中，就将其加入子图
                if (edge.id not in subgraph.edges and 
                    edge.start_node_id in subgraph.nodes and 
                    edge.end_node_id in subgraph.nodes):
                    # 复制边对象
                    new_edge = edge.model_copy(deep=True)
                    subgraph.add_edge(new_edge)
 
        return subgraph

    def get_top_k_tags(self, top_k: int = 10) -> List[Tuple[str, int]]:
        """
        统计所有节点中最常出现的标签。

        Args:
            top_k (int): 返回排名前 k 的标签。

        Returns:
            List[Tuple[str, int]]: 一个元组列表，每个元组包含标签和其出现次数。
        """
        from collections import Counter
        
        all_tags = [tag for node in self.nodes.values() for tag in node.tags]
        if not all_tags:
            return []
            
        tag_counts = Counter(all_tags)
        return tag_counts.most_common(top_k)
