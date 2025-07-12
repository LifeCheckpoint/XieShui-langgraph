from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class AddNodeSchema(BaseModel):
    '''
    使用此工具创建一个知识图谱的节点
    你将为这个节点拟写一个符合情况的名字
    然后为这个节点添加适当描述与内容
    如果你需要添加入边与出边列表，即和本节点相关联的知识点节点，请调用add_edge
    
    Example:
    
    1.关于导数这个知识点的节点
    title：导数
    description：导数是描述函数在这一点的变化趋势
    
    
    '''
    title: str = Field(description='给这个节点一个称呼')
    description: Optional[str] = Field(default=None,description='描述这个节点的定义以及属性')
    
    
@tool('add_a_node',args_schema=AddNodeSchema)
def add_a_node(
    title: str = None,
    description: Optional[str] = None
    ):
    node = Knowledge_Node(title,description)
    
    graph = Knowledge_Graph()
    try:
        graph.add_node(node)
        return f'添加节点{node.title}成功'
    except ValueError as v:
        return f'添加节点失败，原因:{v}'
    except Exception as e:
        return f'添加节点失败，原因:{e}'
