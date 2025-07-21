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

PROMPT_NO_CURRENT_GRAPH = """
## 操作失败
错误: 当前未选择任何知识图谱。
请先使用 `set_current_graph` 或 `add_graph` 工具来选择或创建一个图谱。
"""

PROMPT_OPERATION_ERROR = """
## 操作失败
错误: {{ error_message }}

## 进一步操作提示
请检查你的输入参数或图谱状态，然后重试。
"""
"""
Args:
    error_message (str): 发生的具体错误信息。
"""

PROMPT_ADD_NODE = """
{% if success %}
## 节点添加成功
已成功向图谱 `{{ graph_name }}` 中添加新节点。

节点信息:
- ID: {{ node.id }}
- 标题: {{ node.title }}
- 描述: {{ node.description or '无' }}

## 进一步操作提示
你可以继续添加节点、添加边，或使用 `get_node_info` 工具查看节点详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    node (Knowledge_Node): 新添加的节点对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_ADD_EDGE = """
{% if success %}
## 边添加成功
已成功在图谱 `{{ graph_name }}` 中添加新边。

边信息:
- ID: {{ edge.id }}
- 标题: {{ edge.title }}
- 描述: {{ edge.description or '无' }}
- 起始节点: {{ edge.start_node_id }} ({{ edge.start_node.title }})
- 结束节点: {{ edge.end_node_id }} ({{ edge.end_node.title }})

## 进一步操作提示
你可以继续添加边、节点，或使用 `get_edge_info` 工具查看边的详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    edge (Knowledge_Edge): 新添加的边对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_GET_NODE = """
{% if success %}
## 节点信息查询成功
在图谱 `{{ graph_name }}` 中找到节点 `{{ node_id }}`。

节点详细信息:
- ID: {{ node.id }}
- 标题: {{ node.title }}
- 描述: {{ node.description or '无' }}
- 入边数量: {{ node.in_edge | length }}
- 出边数量: {{ node.out_edge | length }}

## 进一步操作提示
你可以使用 `get_node_in_out_edges` 查看具体边信息，或使用 `get_node_neighbours` 查看邻居节点。
{% elif not_found %}
## 查询结果
在图谱 `{{ graph_name }}` 中未找到 ID 为 `{{ node_id }}` 的节点。

## 进一步操作提示
请使用 `get_all_node` 工具检查所有可用节点的ID。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    not_found (bool): 是否因为未找到而失败。
    graph_name (str): 当前图谱的名称。
    node_id (str): 查询的节点ID。
    node (Knowledge_Node): 查找到的节点对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_GET_EDGE = """
{% if success %}
## 边信息查询成功
在图谱 `{{ graph_name }}` 中找到边 `{{ edge_id }}`。

边详细信息:
- ID: {{ edge.id }}
- 标题: {{ edge.title }}
- 描述: {{ edge.description or '无' }}
- 起始节点: {{ edge.start_node_id }} ({{ edge.start_node.title }})
- 结束节点: {{ edge.end_node_id }} ({{ edge.end_node.title }})

## 进一步操作提示
你可以使用 `get_node_info` 查看相关节点的详细信息。
{% elif not_found %}
## 查询结果
在图谱 `{{ graph_name }}` 中未找到 ID 为 `{{ edge_id }}` 的边。

## 进一步操作提示
请使用 `get_all_edge` 工具检查所有可用边的ID。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    not_found (bool): 是否因为未找到而失败。
    graph_name (str): 当前图谱的名称。
    edge_id (str): 查询的边ID。
    edge (Knowledge_Edge): 查找到的边对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_GET_IN_OUT_EDGES = """
{% if success %}
## 节点边信息查询成功
节点 `{{ node_id }}` ({{ node.title }}) 在图谱 `{{ graph_name }}` 中的边信息如下：

### 入边 ({{ in_edges | length }} 条)
{% if in_edges %}
| 边 ID | 边标题 | 起始节点 ID | 起始节点标题 |
|---|---|---|---|
{% for edge in in_edges %}
| {{ edge.id }} | {{ edge.title }} | {{ edge.start_node_id }} | {{ edge.start_node.title }} |
{% endfor %}
{% else %}
无入边。
{% endif %}

### 出边 ({{ out_edges | length }} 条)
{% if out_edges %}
| 边 ID | 边标题 | 结束节点 ID | 结束节点标题 |
|---|---|---|---|
{% for edge in out_edges %}
| {{ edge.id }} | {{ edge.title }} | {{ edge.end_node_id }} | {{ edge.end_node.title }} |
{% endfor %}
{% else %}
无出边。
{% endif %}

## 进一步操作提示
你可以使用 `get_edge_info` 查看具体边的描述信息。
{% elif not_found %}
## 查询结果
在图谱 `{{ graph_name }}` 中未找到 ID 为 `{{ node_id }}` 的节点。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    not_found (bool): 是否因为未找到节点而失败。
    graph_name (str): 当前图谱的名称。
    node_id (str): 查询的节点ID。
    node (Knowledge_Node): 查询的节点对象。
    in_edges (List[Knowledge_Edge]): 入边列表。
    out_edges (List[Knowledge_Edge]): 出边列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_GET_NEIGHBOURS = """
{% if success %}
## 节点邻居查询成功
节点 `{{ node_id }}` ({{ node.title }}) 在图谱 `{{ graph_name }}` 中的邻居节点如下：

### 邻居节点 ({{ neighbours | length }} 个)
{% if neighbours %}
| 节点 ID | 节点标题 | 描述 |
|---|---|---|
{% for neighbour in neighbours %}
| {{ neighbour.id }} | {{ neighbour.title }} | {{ neighbour.description or '无' }} |
{% endfor %}
{% else %}
该节点没有邻居。
{% endif %}

## 进一步操作提示
你可以使用 `get_node_info` 查看具体邻居节点的详细信息，或使用 `find_path` 查找路径。
{% elif not_found %}
## 查询结果
在图谱 `{{ graph_name }}` 中未找到 ID 为 `{{ node_id }}` 的节点。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    not_found (bool): 是否因为未找到节点而失败。
    graph_name (str): 当前图谱的名称。
    node_id (str): 查询的节点ID。
    node (Knowledge_Node): 查询的节点对象。
    neighbours (List[Knowledge_Node]): 邻居节点列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""