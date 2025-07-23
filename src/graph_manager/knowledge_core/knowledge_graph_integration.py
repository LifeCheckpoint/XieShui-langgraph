from __future__ import annotations

from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
import random
import networkx as nx
import json
import jinja2

from src.graph_manager.knowledge_core.node_edge import Knowledge_Node, Knowledge_Edge
from src.graph_manager.knowledge_core.knowledge_graph import Knowledge_Graph
from src.graph_manager.knowledge_core.prompt import *

# 需要进行持久状态留存

class KnowledgeGraphIntegration:
    """
    知识图谱集成类

    返回消息可直接与 LLMs 进行交互
    """

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
                "top_tags": self.current_graph.get_top_k_tags(10),
            })

    def __init__(self, graph_dir: Optional[str | Path] = None):
        """
        初始化 KnowledgeGraphIntegration
        """
        self.graph_list: List[Knowledge_Graph] = []
        self.current_graph: Optional[Knowledge_Graph] = None
        self.reload_graphs(graph_dir)

    def reload_graphs(self, graph_dir: Optional[str | Path] = None) -> str:
        """
        重新加载知识图谱
        """
        err_load_list = []

        if not graph_dir:
            graph_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_graphs"
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
        
    def add_graph(self, graph_name: str, graph: Optional[Knowledge_Graph] = None) -> str:
        """
        添加一个新的知识图谱到集成中，并保存到文件
        Args:
            name (str): 图谱的名称
            graph (Knowledge_Graph): 要添加的知识图谱
        """
        if not graph:
            graph = Knowledge_Graph(name=graph_name)

        if not isinstance(graph, Knowledge_Graph):
            raise TypeError("graph must be an instance of Knowledge_Graph")

        try:
            self.graph_list.append(graph)
            file_path = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_graphs" / f"{graph_name}.json"
            graph.save_to_file(file_path)
            self.current_graph = graph

            return jinja2.Template(PROMPT_ADD_GRAPH).render({
                "graph": graph
            })
        except Exception as e:
            print(f"Error adding graph: {e}")
            return f"添加图谱失败，错误原因: {e}"
        
    def list_current_graph(self) -> str:
        """
        列出所有存在的知识图谱
        """
        if not self.graph_list:
            return jinja2.Template(PROMPT_LIST_GRAPHS).render({
                "graph_list": [],
                "empty": True
            })
        
        return jinja2.Template(PROMPT_LIST_GRAPHS).render({
            "graph_list": self.graph_list,
            "empty": False
        })

    def set_current_graph(self, name: str) -> str:
        """
        设置当前操作的知识图谱。

        Args:
            name (str): 要设置为当前图谱的名称。

        Returns:
            str: 操作结果的提示信息。
        """
        for graph in self.graph_list:
            if graph.name == name:
                self.current_graph = graph
                return f"已成功切换到知识图谱: {name}"
        
        return jinja2.Template(PROMPT_SET_GRAPH_FAILED).render({
            "name": name,
            "graph_list": self.graph_list
        })

    def add_node_to_current_graph(self, title: str, description: Optional[str] = None, id: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """
        向当前选中的图谱中添加一个新节点。

        Args:
            title (str): 节点的标题。
            description (Optional[str]): 节点的描述。
            id (Optional[str], optional): 节点的ID。如果未提供，将自动生成。默认为 None。
            tags (Optional[List[str]], optional): 节点的标签列表。默认为 None。

        Returns:
            str: 一个为LLM格式化的、包含操作结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            node_data = {"title": title, "description": description}
            if id:
                node_data["id"] = id
            if tags:
                node_data["tags"] = tags
            node = Knowledge_Node(**node_data)
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

    def add_edge_to_current_graph(self, start_node_id: str, end_node_id: str, title: str, description: Optional[str] = None, id: Optional[str] = None) -> str:
        """
        向当前选中的图谱中添加一条新边。

        Args:
            start_node_id (str): 起始节点的ID。
            end_node_id (str): 结束节点的ID。
            title (str): 边的标题。
            description (Optional[str]): 边的描述。
            id (Optional[str], optional): 边的ID。如果未提供，将自动生成。默认为 None。

        Returns:
            str: 一个为LLM格式化的、包含操作结果的字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            edge_data = {
                "start_node_id": start_node_id,
                "end_node_id": end_node_id,
                "title": title,
                "description": description
            }
            if id:
                edge_data["id"] = id
            edge = Knowledge_Edge(**edge_data)
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

    def search_nodes_by_tag(self, tags: List[str], mode: str = 'AND', case_sensitive: bool = False) -> str:
        """
        根据一个或多个标签搜索节点。

        Args:
            tags (List[str]): 要搜索的标签列表。
            mode (str): 搜索模式，'AND' 或 'OR'。
            case_sensitive (bool): 是否区分大小写。

        Returns:
            str: 格式化后的搜索结果。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            found_nodes = self.current_graph.search_nodes_by_tag(tags, mode, case_sensitive)
            return jinja2.Template(PROMPT_SEARCH_NODES_BY_TAG).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "tags": tags,
                "mode": mode,
                "count": len(found_nodes),
                "nodes": found_nodes
            })
        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_SEARCH_NODES_BY_TAG).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })

    def find_path(self, start_node_id: str, end_node_id: str, with_description: bool = False, with_edge_description: bool = False) -> str:
        """
        查找两个节点之间的最短路径，并返回包含路径信息的prompt。

        Args:
            start_node_id (str): 起始节点的ID。
            end_node_id (str): 结束节点的ID。
            with_description (bool, optional): 是否在结果中包含路径上节点的描述。默认为 False。
            with_edge_description (bool, optional): 是否在结果中包含路径上边的描述。默认为 False。

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            path_node_ids = self.current_graph.find_path(start_node_id, end_node_id)

            if not path_node_ids:
                return jinja2.Template(PROMPT_FIND_PATH).render({
                    "success": False,
                    "not_found": True,
                    "graph_name": self.current_graph.name,
                    "start_node_id": start_node_id,
                    "end_node_id": end_node_id
                })

            G = self.current_graph._to_networkx()
            centrality = nx.betweenness_centrality(G, normalized=True)

            path_nodes_info = []
            for node_id in path_node_ids:
                node = self.current_graph.get_node(node_id)
                path_nodes_info.append({
                    "node": node,
                    "in_degree": G.in_degree(node_id),
                    "out_degree": G.out_degree(node_id),
                    "centrality": centrality.get(node_id, 0.0)
                })

            path_edges = []
            for i in range(len(path_node_ids) - 1):
                u_id = path_node_ids[i]
                v_id = path_node_ids[i+1]
                # Find the edge(s) connecting u and v
                for edge in self.current_graph.get_out_edge(u_id):
                    if edge.end_node_id == v_id:
                        path_edges.append(edge)
                        break # Assuming one edge, for simplicity

            return jinja2.Template(PROMPT_FIND_PATH).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "start_node_id": start_node_id,
                "end_node_id": end_node_id,
                "path_nodes": path_nodes_info,
                "path_edges": path_edges,
                "with_description": with_description,
                "with_edge_description": with_edge_description
            })

        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_FIND_PATH).render({
                "success": False,
                "not_found": False,
                "graph_name": self.current_graph.name,
                "start_node_id": start_node_id,
                "end_node_id": end_node_id,
                "error_prompt": error_prompt
            })

    def delete_items(self, node_ids: Optional[List[str]] = None, edge_ids: Optional[List[str]] = None) -> str:
        """
        通过ID批量删除节点和边。

        Args:
            node_ids (Optional[List[str]], optional): 要删除的节点ID列表。默认为 None。
            edge_ids (Optional[List[str]], optional): 要删除的边ID列表。默认为 None。

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        deleted_nodes_count = 0
        deleted_edges_count = 0
        not_found_nodes = []
        not_found_edges = []

        try:
            if node_ids:
                for node_id in node_ids:
                    try:
                        self.current_graph.remove_node(node_id)
                        deleted_nodes_count += 1
                    except ValueError:
                        not_found_nodes.append(node_id)
            
            if edge_ids:
                for edge_id in edge_ids:
                    try:
                        self.current_graph.remove_edge(edge_id)
                        deleted_edges_count += 1
                    except ValueError:
                        not_found_edges.append(edge_id)

            return jinja2.Template(PROMPT_DELETE_ITEMS).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "deleted_nodes_count": deleted_nodes_count,
                "deleted_edges_count": deleted_edges_count,
                "not_found_nodes": not_found_nodes,
                "not_found_edges": not_found_edges
            })

        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_DELETE_ITEMS).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })
    
    def update_node_in_current_graph(self, node_id: str, title: Optional[str] = None, description: Optional[str] = None, tags: Optional[List[str]] = None) -> str:
        """
        更新当前图谱中指定ID的节点信息。

        Args:
            node_id (str): 要更新的节点ID。
            title (Optional[str], optional): 新的节点标题。
            description (Optional[str], optional): 新的节点描述。
            tags (Optional[List[str]], optional): 新的节点标签列表。

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            # 获取更新前的节点信息
            original_node = self.current_graph.get_node(node_id)
            if not original_node:
                raise ValueError(f"节点 ID {node_id} 不存在")
            
            original_node_copy = original_node.model_copy(deep=True)

            self.current_graph.update_node(node_id, title, description, tags)
            
            # 获取更新后的节点信息
            updated_node = self.current_graph.get_node(node_id)

            return jinja2.Template(PROMPT_UPDATE_NODE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "original_node": original_node_copy,
                "updated_node": updated_node
            })

        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_UPDATE_NODE).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "node_id": node_id,
                "error_prompt": error_prompt
            })

    def update_edge_in_current_graph(self, edge_id: str, title: Optional[str] = None, description: Optional[str] = None) -> str:
        """
        更新当前图谱中指定ID的边信息。

        Args:
            edge_id (str): 要更新的边ID。
            title (Optional[str], optional): 新的边标题。
            description (Optional[str], optional): 新的边描述。

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            # 获取更新前的边信息
            original_edge = self.current_graph.get_edge(edge_id)
            if not original_edge:
                raise ValueError(f"边 ID {edge_id} 不存在")
            
            original_edge_copy = original_edge.model_copy(deep=True)

            self.current_graph.update_edge(edge_id, title, description)
            
            # 获取更新后的边信息
            updated_edge = self.current_graph.get_edge(edge_id)

            return jinja2.Template(PROMPT_UPDATE_EDGE).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "edge_id": edge_id,
                "original_edge": original_edge_copy,
                "updated_edge": updated_edge
            })

        except ValueError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_UPDATE_EDGE).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "edge_id": edge_id,
                "error_prompt": error_prompt
            })

    def batch_add_from_json(self, json_data: str) -> str:
        """
        通过JSON数据批量添加节点和边。

        Args:
            json_data (str): 包含节点和边列表的JSON字符串。

        JSON格式要求:
        - 顶层是一个对象，包含 "nodes" 和/或 "edges" 键。
        - "nodes" 是一个节点对象列表。
          - 每个节点对象必须包含:
            - "title": str (可选, 默认为 "Node")
            - "description": str (可选)
            - "id": str (可选, 如果不提供会自动生成)
            - "tags": List[str] (可选)
        - "edges" 是一个边对象列表。
          - 每个边对象必须包含:
            - "start_node_id": str (必需)
            - "end_node_id": str (必需)
            - "title": str (可选, 默认为 "Edge")
            - "description": str (可选)
            - "id": str (可选, 如果不提供会自动生成)

        JSON示例:
        ```json
        {
          "nodes": [
            {
              "id": "node_1",
              "title": "大语言模型",
              "description": "一种先进的人工智能模型",
              "tags": ["AI", "LLM"]
            },
            {
              "id": "node_2",
              "title": "知识图谱"
            }
          ],
          "edges": [
            {
              "start_node_id": "node_1",
              "end_node_id": "node_2",
              "title": "应用于"
            }
          ]
        }
        ```

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        added_nodes_count = 0
        added_edges_count = 0
        errors = []

        try:
            data = json.loads(json_data)
            
            # Add nodes first
            if 'nodes' in data and isinstance(data['nodes'], list):
                for node_data in data['nodes']:
                    try:
                        node = Knowledge_Node(**node_data)
                        self.current_graph.add_node(node)
                        added_nodes_count += 1
                    except (ValueError, TypeError) as e:
                        errors.append({"item": str(node_data), "message": str(e)})

            # Then add edges
            if 'edges' in data and isinstance(data['edges'], list):
                for edge_data in data['edges']:
                    try:
                        edge = Knowledge_Edge(**edge_data)
                        self.current_graph.add_edge(edge)
                        added_edges_count += 1
                    except (ValueError, TypeError) as e:
                        errors.append({"item": str(edge_data), "message": str(e)})

            return jinja2.Template(PROMPT_BATCH_ADD).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "added_nodes_count": added_nodes_count,
                "added_edges_count": added_edges_count,
                "errors": errors
            })

        except json.JSONDecodeError as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": f"JSON解析失败: {e}"})
            return jinja2.Template(PROMPT_BATCH_ADD).render({"success": False, "error_prompt": error_prompt})
        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_BATCH_ADD).render({
                "success": False,
                "graph_name": self.current_graph.name if self.current_graph else "Unknown",
                "error_prompt": error_prompt
            })

    def sample_nodes(self, count: int = 5) -> str:
        """
        从图中随机采样指定数量的节点。

        Args:
            count (int, optional): 要采样的节点数量。默认为 5。

        Returns:
            str: 渲染后的prompt字符串。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            all_nodes = list(self.current_graph.nodes.values())
            if count > len(all_nodes):
                count = len(all_nodes)
            
            sampled_nodes = random.sample(all_nodes, count)

            return jinja2.Template(PROMPT_SAMPLE_NODES).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "count": count,
                "sampled_nodes": sampled_nodes
            })

        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_SAMPLE_NODES).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })

    def get_all_node(self) -> str:
        """
        获取当前图谱中所有节点的简要信息（ID和标题）。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()
        
        nodes = self.current_graph.get_all_node()
        node_briefs = [{"id": node.id, "title": node.title} for node in nodes]
        
        return jinja2.Template(PROMPT_ALL_NODES).render({
            "graph_name": self.current_graph.name,
            "count": len(nodes),
            "nodes": node_briefs
        })

    def get_all_edge(self) -> str:
        """
        获取当前图谱中所有边的简要信息（ID和标题）。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()
            
        edges = self.current_graph.get_all_edge()
        edge_briefs = [{"id": edge.id, "title": edge.title} for edge in edges]
        
        return jinja2.Template(PROMPT_ALL_EDGES).render({
            "graph_name": self.current_graph.name,
            "count": len(edges),
            "edges": edge_briefs
        })

    def summarize_graph_content(self, max_nodes: int = 10, max_edges: int = 10) -> str:
        """
        通过随机采样，为LLM提供当前知识图谱的高层次摘要。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            node_count = len(self.current_graph.nodes)
            edge_count = len(self.current_graph.edges)

            top_in_degree_nodes = self.current_graph.get_high_in_degree_nodes(max_nodes)
            top_out_degree_nodes = self.current_graph.get_high_out_degree_nodes(max_nodes)
            top_betweenness_centrality_nodes = self.current_graph.get_high_betweenness_centrality_nodes(max_nodes)

            all_edges = self.current_graph.get_all_edge()
            sampled_edges = random.sample(all_edges, min(len(all_edges), max_edges))

            return jinja2.Template(PROMPT_SUMMARIZE_GRAPH).render({
                "success": True,
                "graph_name": self.current_graph.name,
                "node_count": node_count,
                "edge_count": edge_count,
                "top_in_degree_nodes": top_in_degree_nodes,
                "top_out_degree_nodes": top_out_degree_nodes,
                "top_betweenness_centrality_nodes": top_betweenness_centrality_nodes,
                "sampled_edges": sampled_edges,
                "top_tags": self.current_graph.get_top_k_tags(max_nodes)
            })
        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_SUMMARIZE_GRAPH).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })
    
    def save_current_graph(self) -> str:
        """
        保存当前图谱到文件。
        """
        if not self.current_graph:
            return jinja2.Template(PROMPT_NO_CURRENT_GRAPH).render()

        try:
            # 使用 reload_graphs 中定义的默认路径
            graph_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_graphs"
            if not graph_dir.exists():
                graph_dir.mkdir(parents=True, exist_ok=True)
            
            file_path = graph_dir / f"{self.current_graph.name}.json"
            self.current_graph.save_to_file(str(file_path))
            return jinja2.Template(PROMPT_SAVE_GRAPH).render({
                "success": True,
                "graph_name": self.current_graph.name
            })
        except Exception as e:
            error_prompt = jinja2.Template(PROMPT_OPERATION_ERROR).render({"error_message": str(e)})
            return jinja2.Template(PROMPT_SAVE_GRAPH).render({
                "success": False,
                "graph_name": self.current_graph.name,
                "error_prompt": error_prompt
            })

    def save_all_graphs(self) -> str:
        """
        保存所有已加载的知识图谱到文件。
        """
        if not self.graph_list:
            return jinja2.Template(PROMPT_NO_GRAPHS_TO_SAVE).render()

        saved_graphs = []
        failed_graphs = []
        
        # 使用 reload_graphs 中定义的默认路径
        graph_dir = Path(__file__).parent.parent.parent.parent / "data" / "knowledge_graphs"
        if not graph_dir.exists():
            graph_dir.mkdir(parents=True, exist_ok=True)

        for graph in self.graph_list:
            try:
                file_path = graph_dir / f"{graph.name}.json"
                graph.save_to_file(str(file_path))
                saved_graphs.append(graph.name)
            except Exception as e:
                failed_graphs.append({"name": graph.name, "error": str(e)})
        
        return jinja2.Template(PROMPT_SAVE_ALL_GRAPHS).render({
            "saved_graphs": saved_graphs,
            "failed_graphs": failed_graphs
        })