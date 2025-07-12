from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class AddEdgeSchema(BaseModel):
    
    title:str = Field(description='')
    start_node_id:str = Field(description='')
    end_node_if :str = Field(description='')
    

@tool('add_a_edge',args_schema=AddEdgeSchema)
def add_a_edge(
    title: str = None,
    description: Optional[str] = None,
    in_edge: List[str] = [],
    out_edge: List[str] = []
):
    edge = Knowledge_Edge(title,description,in_edge,out_edge)
    
    graph = Knowledge_Graph()
    try:
        graph.add_edge(edge)
        return f'添加边{edge.title}成功'
    except ValueError as v:
        return f'添加节点失败，原因:{v}'
    except Exception as e:
        return f'添加边失败，原因:{e}'