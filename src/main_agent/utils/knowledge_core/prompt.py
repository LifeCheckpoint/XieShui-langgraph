PROMPT_GRAPH_STRUCTURE = """
{% raw %}
你所操作的知识图谱结构如下:
```python
class Knowledge_Node(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(default="Node")
    description: Optional[str] = Field(default=None)
    in_edge: List[str] = Field(default_factory=list)  # 入边列表
    out_edge: List[str] = Field(default_factory=list)  # 出边列表

class Knowledge_Edge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    title: str = Field(default="Edge")
    start_node_id: str
    end_node_id: str
    description: Optional[str] = Field(default=None)

class Knowledge_Graph(BaseModel):
    ...
```python

## 进一步操作提示
你可以通过一系列工具与知识图谱进行交互，建议全面了解图谱的信息与结构后执行操作
{% endraw %}
"""

PROMPT_STR = """
{% if selected %}
## 当前图谱信息
图谱名称: {{ name }}

统计数据:
- 节点数量: {{ node_count }}, 边数量: {{ edge_count }}
- 入度最高前10节点: {{ top_in_degree_nodes }}
- 出度最高前10节点: {{ top_out_degree_nodes }}
- 介数中心性最高前10节点: {{ top_betweenness_centrality_nodes }}
- 接近中心性最高前10节点: {{ top_closeness_centrality_nodes }}

## 进一步操作提示
你可以通过一系列工具与知识图谱进行交互，建议全面了解图谱的信息与结构后执行操作
{% else %}
## 当前未选择图谱，请先可以选择图谱后调用此工具获得图谱信息
{% endif %}
"""
"""
Args:
    selected (bool): 是否有选中的图谱
    name (str): 图谱名称
    node_count (int): 节点数量
    edge_count (int): 边数量
    top_in_degree_nodes (List[Tuple[str, int]]): 入度最高前10节点
    top_out_degree_nodes (List[Tuple[str, int]]): 出度最高前10节点
    top_betweenness_centrality_nodes (List[Tuple[str, int]]): 介数中心性最高前10节点
    top_closeness_centrality_nodes (List[Tuple[str, int]]): 接近中心性最高前10节点
"""

PROMPT_RELOAD_GRAPHS = """
知识图谱已重新加载，当前知识图谱列表:
{% for graph in graph_list %}
- {{ graph.name }}
{% endfor %}

{% if err_load_list %}
加载失败图谱列表:
{% for err in err_load_list %}
- {{ err }}
{% endfor %}
{% endif %}

## 进一步操作提示
当前未切换到特定图谱，可使用相关工具设置当前图谱
"""
"""
Args:
    graph_list (List[KnowledgeGraph]): 图谱列表
    err_load_list (List[str]): 错误列表
"""

PROMPT_ADD_GRAPH = """
添加图谱成功，图谱名称: {{ graph.name }}
已自动切换到当前图谱

## 进一步操作提示
如果创建空白图谱，图谱内将没有节点和边。可使用相关方法添加
"""
"""
Args:
    graph (KnowledgeGraph): 新添加的图谱
"""