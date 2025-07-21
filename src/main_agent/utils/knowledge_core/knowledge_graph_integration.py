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