from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple, Callable
from collections import deque
from pathlib import Path
import networkx as nx
import json
import jinja2

from src.main_agent.utils.knowledge_core.node_edge import Knowledge_Node, Knowledge_Edge
from src.main_agent.utils.knowledge_core.knowledge_graph import Knowledge_Graph
from src.main_agent.utils.knowledge_core.prompt import *

# 需要进行持久状态留存

class KnowledgeGraphIntegration:
    """
    知识图谱集成类

    返回消息可直接与 LLMs 进行交互
    """
    graph_list: List[Knowledge_Graph] = []
    current_graph: Optional[Knowledge_Graph] = None

    def __repr__(self):
        return "KnowledgeGraphIntegration"
    
    def __str__(self):
        if not self.current_graph:
            return jinja2.Template(PROMPT_STR).render({"selected": False})
        else:
            node_rank_title: Callable[[List[Tuple[Knowledge_Node, int]]], List[Tuple[str, int]]] = lambda li: [
                (node.title, degree) for node, degree in li
            ]
            return jinja2.Template(PROMPT_STR).render({
                "selected": True,
                "name": self.current_graph.name,
                "node_count": len(self.current_graph.nodes),
                "edge_count": len(self.current_graph.edges),
                "top_in_degree_nodes": node_rank_title(self.current_graph.get_high_in_degree_nodes(10)),
                "top_out_degree_nodes": node_rank_title(self.current_graph.get_high_out_degree_nodes(10)),
                "top_betweenness_centrality_nodes": node_rank_title(self.current_graph.get_high_betweenness_centrality_nodes(10)),
                "top_closeness_centrality_nodes": node_rank_title(self.current_graph.get_high_closeness_centrality_nodes(10)),
            })

    def __init__(self, graph_dir: Optional[str | Path] = None):
        """
        初始化 KnowledgeGraphIntegration
        """
        self.reload_graphs(graph_dir)

    def reload_graphs(self, graph_dir: Optional[str | Path] = None) -> str:
        """
        重新加载知识图谱
        """
        err_load_list = []

        if not graph_dir:
            graph_dir = Path(__file__).parent.parent.parent / "data" / "knowledge_graphs"
        if isinstance(graph_dir, str):
            graph_dir = Path(graph_dir)
        if not graph_dir.exists():
            graph_dir.mkdir(parents=True, exist_ok=True)

        self.graph_list.clear()
        graph_files = list(graph_dir.glob("*.json"))
        for graph_file in graph_files:
            try:
                loading_graph = Knowledge_Graph.load_from_file(str(graph_file))
                self.graph_list.append(loading_graph)
            except Exception as e:
                print(f"Error loading graph from {graph_file}: {e}")
                err_load_list.append(str(graph_file))
                continue

        return jinja2.Template(PROMPT_RELOAD_GRAPHS).render({
            "graph_list": self.graph_list,
            "err_load_list": err_load_list
        })
        
    def add_graph(self, filename: str, graph: Optional[Knowledge_Graph] = None) -> str:
        """
        添加一个新的知识图谱到集成中，并保存到文件
        Args:
            name (str): 图谱的名称
            graph (Knowledge_Graph): 要添加的知识图谱
        """
        if not graph:
            graph = Knowledge_Graph(name=filename)

        if not isinstance(graph, Knowledge_Graph):
            raise TypeError("graph must be an instance of Knowledge_Graph")

        try:
            self.graph_list.append(graph)
            graph.save_to_file(filename)
            self.current_graph = graph

            return jinja2.Template(PROMPT_ADD_GRAPH).render({
                "graph": graph
            })
        except Exception as e:
            print(f"Error adding graph: {e}")
            return f"添加图谱失败，错误原因: {e}"

    def add_node_to_current_graph(self, title: str, description: Optional[str] = None) -> str:
        """
        向当前选中的图谱中添加一个新节点。

        Args:
            title (str): 节点的标题。
            description (Optional[str]): 节点的描述。

        Returns:
            str: 一个为LLM格式化的、包含操作结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            node = Knowledge_Node(title=title, description=description)
            self.current_graph.add_node(node)
            return jinja2.Template(PROMPT_ADD_NODE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node": node
            })
        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_ADD_NODE).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })

    def add_edge_to_current_graph(self, start_node_id: str, end_node_id: str, title: str, description: Optional[str] = None) -> str:
        """
        向当前选中的图谱中添加一条新边。

        Args:
            start_node_id (str): 起始节点的ID。
            end_node_id (str): 结束节点的ID。
            title (str): 边的标题。
            description (Optional[str]): 边的描述。

        Returns:
            str: 一个为LLM格式化的、包含操作结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            edge = Knowledge_Edge(
                start_node_id=start_node_id,
                end_node_id=end_node_id,
                title=title,
                description=description
            )
            self.current_graph.add_edge(edge)
            return jinja2.Template(PROMPT_ADD_EDGE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "edge": edge
            })
        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_ADD_EDGE).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })

    def get_node_info(self, node_id: str) -> str:
        """
        获取当前图谱中指定ID的节点信息。

        Args:
            node_id (str): 要查询的节点ID。

        Returns:
            str: 一个为LLM格式化的、包含查询结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        node = self.current_graph.get_node(node_id)
        if node:
            return jinja2.Template(PROMPT_GET_NODE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "node": node
            })
        else:
            return jinja2.Template(PROMPT_GET_NODE).render({
                "success": False,
                "not_found": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id
            })

    def get_edge_info(self, edge_id: str) -> str:
        """
        获取当前图谱中指定ID的边信息。

        Args:
            edge_id (str): 要查询的边ID。

        Returns:
            str: 一个为LLM格式化的、包含查询结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        edge = self.current_graph.get_edge(edge_id)
        if edge:
            return jinja2.Template(PROMPT_GET_EDGE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "edge_id": edge_id,
                "edge": edge
            })
        else:
            return jinja2.Template(PROMPT_GET_EDGE).render({
                "success": False,
                "not_found": True,
                "graph_name": self.current_graph.name,
                "edge_id": edge_id
            })

    def get_node_in_out_edges(self, node_id: str) -> str:
        """
        获取当前图谱中指定节点的所有入边和出边信息。

        Args:
            node_id (str): 要查询的节点ID。

        Returns:
            str: 一个为LLM格式化的、包含查询结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        node = self.current_graph.get_node(node_id)
        if not node:
            return jinja2.Template(PROMPT_GET_IN_OUT_EDGES).render({
                "success": False,
                "not_found": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id
            })

        try:
            in_edges = self.current_graph.get_in_edge(node_id)
            out_edges = self.current_graph.get_out_edge(node_id)
            return jinja2.Template(PROMPT_GET_IN_OUT_EDGES).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "node": node,
                "in_edges": in_edges,
                "out_edges": out_edges
            })
        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_GET_IN_OUT_EDGES).render({
                "success": False,
                "not_found": False,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "error_prompt": error_prompt
            })

    def get_node_neighbours(self, node_id: str) -> str:
        """
        获取当前图谱中指定节点的所有邻居节点信息。

        Args:
            node_id (str): 要查询的节点ID。

        Returns:
            str: 一个为LLM格式化的、包含查询结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        node = self.current_graph.get_node(node_id)
        if not node:
            return jinja2.Template(PROMPT_GET_NEIGHBOURS).render({
                "success": False,
                "not_found": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id
            })

        try:
            neighbours = self.current_graph.get_neighbours(node_id)
            return jinja2.Template(PROMPT_GET_NEIGHBOURS).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "node": node,
                "neighbours": neighbours
            })
        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_GET_NEIGHBOURS).render({
                "success": False,
                "not_found": False,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "error_prompt": error_prompt
            })