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
```

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
- 最常出现的10个标签: {{ top_tags }}

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
    top_tags (List[Tuple[str, int]]): 最常出现的标签
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

PROMPT_SET_GRAPH_FAILED = """
## 切换图谱失败
未能找到名为 `{{ name }}` 的知识图谱。

**当前可用的图谱列表:**
{% if graph_list %}
{% for graph in graph_list %}
- `{{ graph.name }}`
{% endfor %}
{% else %}
- 当前没有已加载的图谱。
{% endif %}

## 进一步操作提示
- 请检查你输入的名称是否正确。
- 如果你认为图谱文件存在但未加载，可以尝试使用 `reload_graphs` 工具重新加载所有图谱。
"""
"""
Args:
    name (str): 尝试切换的图谱名称。
    graph_list (List[KnowledgeGraph]): 当前已加载的图谱列表。
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
- 标签: {{ node.tags | join(', ') if node.tags else '无' }}

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
- 标签: {{ node.tags | join(', ') if node.tags else '无' }}
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

PROMPT_FIND_PATH = """
{% if success %}
## 路径查找成功

在知识图谱 **{{ graph_name }}** 中，从节点 **{{ start_node_id }}** 到 **{{ end_node_id }}** 的路径如下：

**路径节点:**
{% for node_info in path_nodes %}
- **ID:** {{ node_info.node.id }}
  - **标题:** {{ node_info.node.title }}
  - **入度:** {{ node_info.in_degree }}
  - **出度:** {{ node_info.out_degree }}
  - **中心度:** {{ "%.4f"|format(node_info.centrality) }}
  - **标签:** {{ node_info.node.tags | join(', ') if node_info.node.tags else '无' }}
  {% if with_description and node_info.node.description %}
  - **描述:** {{ node_info.node.description }}
  {% endif %}
{% endfor %}

**路径边:**
{% for edge in path_edges %}
- **ID:** {{ edge.id }}
  - **标题:** {{ edge.title }}
  - **从:** {{ edge.start_node_id }}
  - **到:** {{ edge.end_node_id }}
  {% if with_edge_description and edge.description %}
  - **描述:** {{ edge.description }}
  {% endif %}
{% endfor %}

## 进一步操作提示
你可以使用 `get_node_info` 或 `get_edge_info` 工具来获取更详细的信息。
{% elif not_found %}
## 路径查找结果

在知识图谱 **{{ graph_name }}** 中，无法找到从节点 **{{ start_node_id }}** 到 **{{ end_node_id }}** 的路径。

## 进一步操作提示
请检查节点ID是否正确，或者尝试使用 `get_all_node` 工具来查看所有节点。
{% elif error_prompt %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    not_found (bool): 是否因为未找到路径而失败。
    graph_name (str): 当前图谱的名称。
    start_node_id (str): 起始节点的ID。
    end_node_id (str): 结束节点的ID。
    path_nodes (List[Dict[str, Any]]): 路径上的节点信息列表，每个元素包含 'node', 'in_degree', 'out_degree', 'centrality'。
    path_edges (List[Knowledge_Edge]): 路径上的边列表。
    with_description (bool): 是否包含节点描述。
    with_edge_description (bool): 是否包含边描述。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_DELETE_ITEMS = """
{% if success %}
## 批量删除成功

在知识图谱 **{{ graph_name }}** 中，已成功完成批量删除操作。

**删除统计:**
- **节点:** {{ deleted_nodes_count }} 个
- **边:** {{ deleted_edges_count }} 个

{% if not_found_nodes %}
**未找到的节点ID:**
- {{ not_found_nodes | join(', ') }}
{% endif %}

{% if not_found_edges %}
**未找到的边ID:**
- {{ not_found_edges | join(', ') }}
{% endif %}

## 进一步操作提示
你可以使用 `get_all_node` 或 `get_all_edge` 工具来确认删除结果。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    deleted_nodes_count (int): 成功删除的节点数量。
    deleted_edges_count (int): 成功删除的边数量。
    not_found_nodes (List[str]): 未找到的节点ID列表。
    not_found_edges (List[str]): 未找到的边ID列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_UPDATE_NODE = """
{% if success %}
## 节点更新成功

在知识图谱 **{{ graph_name }}** 中，节点 **{{ node_id }}** 已成功更新。

**更新前:**
- **标题:** {{ original_node.title }}
- **描述:** {{ original_node.description or '无' }}
- **标签:** {{ original_node.tags | join(', ') if original_node.tags else '无' }}

**更新后:**
- **标题:** {{ updated_node.title }}
- **描述:** {{ updated_node.description or '无' }}
- **标签:** {{ updated_node.tags | join(', ') if updated_node.tags else '无' }}

## 进一步操作提示
你可以使用 `get_node_info` 工具来确认更新后的详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    node_id (str): 被更新的节点ID。
    original_node (Knowledge_Node): 更新前的节点对象。
    updated_node (Knowledge_Node): 更新后的节点对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_UPDATE_EDGE = """
{% if success %}
## 边更新成功

在知识图谱 **{{ graph_name }}** 中，边 **{{ edge_id }}** 已成功更新。

**更新前:**
- **标题:** {{ original_edge.title }}
- **描述:** {{ original_edge.description or '无' }}

**更新后:**
- **标题:** {{ updated_edge.title }}
- **描述:** {{ updated_edge.description or '无' }}

## 进一步操作提示
你可以使用 `get_edge_info` 工具来确认更新后的详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    edge_id (str): 被更新的边ID。
    original_edge (Knowledge_Edge): 更新前的边对象。
    updated_edge (Knowledge_Edge): 更新后的边对象。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_BATCH_ADD = """
{% if success %}
## 批量添加成功

在知识图谱 **{{ graph_name }}** 中，已成功完成批量添加操作。

**添加统计:**
- **节点:** {{ added_nodes_count }} 个
- **边:** {{ added_edges_count }} 个

{% if errors %}
**添加失败的条目:**
{% for error in errors %}
- **条目:** `{{ error.item }}`
  - **错误:** {{ error.message }}
{% endfor %}
{% endif %}

## 进一步操作提示
你可以使用 `get_all_node` 或 `get_all_edge` 工具来确认添加结果。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    added_nodes_count (int): 成功添加的节点数量。
    added_edges_count (int): 成功添加的边数量。
    errors (List[Dict[str, Any]]): 添加失败的条目列表，每个元素包含 'item' 和 'message'。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_SAMPLE_NODES = """
{% if success %}
## 随机采样成功

在知识图谱 **{{ graph_name }}** 中，随机采样了 **{{ count }}** 个节点：

{% if sampled_nodes %}
| 节点 ID | 节点标题 | 描述 | 标签 |
|---|---|---|---|
{% for node in sampled_nodes %}
| {{ node.id }} | {{ node.title }} | {{ node.description or '无' }} | {{ node.tags | join(', ') if node.tags else '无' }} |
{% endfor %}
{% else %}
图中没有可供采样的节点。
{% endif %}

## 进一步操作提示
你可以使用 `get_node_info` 查看具体节点的详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    count (int): 请求采样的节点数量。
    sampled_nodes (List[Knowledge_Node]): 采样到的节点列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_SUMMARIZE_GRAPH = """
{% if success %}
## 知识图谱内容摘要: {{ graph_name }}

**核心统计:**
- **节点总数:** {{ node_count }}
- **边总数:** {{ edge_count }}

**核心节点 (基于入度):**
{% if top_in_degree_nodes %}
| 节点ID | 节点标题 | 入度 |
|---|---|---|
{% for node, degree in top_in_degree_nodes %}
| {{ node.id }} | {{ node.title }} | {{ degree }} |
{% endfor %}
{% else %}
- 暂无高入度节点。
{% endif %}

**核心节点 (基于出度):**
{% if top_out_degree_nodes %}
| 节点ID | 节点标题 | 出度 |
|---|---|---|
{% for node, degree in top_out_degree_nodes %}
| {{ node.id }} | {{ node.title }} | {{ degree }} |
{% endfor %}
{% else %}
- 暂无高出度节点。
{% endif %}

**核心节点 (基于介数中心性):**
{% if top_betweenness_centrality_nodes %}
| 节点ID | 节点标题 | 中心性得分 |
|---|---|---|
{% for node, score in top_betweenness_centrality_nodes %}
| {{ node.id }} | {{ node.title }} | {{ "%.4f"|format(score) }} |
{% endfor %}
{% else %}
- 无法计算或暂无高中心性节点。
{% endif %}

**最常出现的标签:**
{% if top_tags %}
| 标签 | 出现次数 |
|---|---|
{% for tag, count in top_tags %}
| {{ tag }} | {{ count }} |
{% endfor %}
{% else %}
- 图中暂无标签。
{% endif %}

**随机边示例:**
{% if sampled_edges %}
| 边ID | 边标题 | 从 ({{ edge.start_node.title }}) | 到 ({{ edge.end_node.title }}) |
|---|---|---|---|
{% for edge in sampled_edges %}
| {{ edge.id }} | {{ edge.title }} | {{ edge.start_node_id }} ({{ edge.start_node.title }}) | {{ edge.end_node_id }} ({{ edge.end_node.title }}) |
{% endfor %}
{% else %}
- 图中暂无边。
{% endif %}

## 进一步操作提示
这是一个图谱内容的快速概览。你可以使用 `get_all_node` 来查看所有节点，或使用 `get_node_info` 来深入了解特定节点。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    node_count (int): 节点总数。
    edge_count (int): 边总数。
    top_in_degree_nodes (List[Tuple[Knowledge_Node, int]]): 入度最高的节点列表。
    top_out_degree_nodes (List[Tuple[Knowledge_Node, int]]): 出度最高的节点列表。
    top_betweenness_centrality_nodes (List[Tuple[Knowledge_Node, float]]): 介数中心性最高的节点列表。
    sampled_edges (List[Knowledge_Edge]): 随机采样的边列表。
    top_tags (List[Tuple[str, int]]): 最常出现的标签列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_SEARCH_NODES_BY_TAG = """
{% if success %}
## 按标签搜索节点成功

在知识图谱 **{{ graph_name }}** 中，使用标签 `{{ tags | join(', ') }}` (模式: {{ mode }}) 搜索到 **{{ count }}** 个节点。

{% if nodes %}
| 节点 ID | 节点标题 | 标签 |
|---|---|---|
{% for node in nodes %}
| {{ node.id }} | {{ node.title }} | {{ node.tags | join(', ') }} |
{% endfor %}
{% else %}
没有找到匹配的节点。
{% endif %}

## 进一步操作提示
你可以使用 `get_node_info` 查看具体节点的详细信息。
{% else %}
{{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    tags (List[str]): 用于搜索的标签列表。
    mode (str): 搜索模式 ('AND' 或 'OR')。
    count (int): 找到的节点数量。
    nodes (List[Knowledge_Node]): 匹配的节点列表。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""

PROMPT_ALL_NODES = """
## 所有节点信息

在知识图谱 **{{ graph_name }}** 中共有 **{{ count }}** 个节点。

{% if nodes %}
| 节点 ID | 节点标题 |
|---|---|
{% for node in nodes %}
| {{ node.id }} | {{ node.title }} |
{% endfor %}
{% else %}
当前图谱中没有节点。
{% endif %}

## 进一步操作提示
你可以使用 `get_node_info` 工具来获取特定节点的详细信息。
"""

PROMPT_ALL_EDGES = """
## 所有边信息

在知识图谱 **{{ graph_name }}** 中共有 **{{ count }}** 条边。

{% if edges %}
| 边 ID | 边标题 |
|---|---|
{% for edge in edges %}
| {{ edge.id }} | {{ edge.title }} |
{% endfor %}
{% else %}
当前图谱中没有边。
{% endif %}

## 进一步操作提示
你可以使用 `get_edge_info` 工具来获取特定边的详细信息。
"""

PROMPT_SAVE_GRAPH = """
{% if success %}
## 图谱保存成功
图谱 **{{ graph_name }}** 已成功保存到文件
{% else %}
图谱 **{{ graph_name }}** 保存失败: {{ error_prompt }}
{% endif %}
"""
"""
Args:
    success (bool): 操作是否成功。
    graph_name (str): 当前图谱的名称。
    error_prompt (str): 如果失败，则传递由 PROMPT_OPERATION_ERROR 生成的错误提示。
"""