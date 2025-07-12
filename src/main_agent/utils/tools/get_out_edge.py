from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class GetOutEdgeSchema(BaseModel):
    node_id:str = Field(description='')
    
@tool('_get_out_edge',args_schema=GetOutEdgeSchema)
def _get_out_edge(node_id:str):
    graph = Knowledge_Graph()
    
    try:
        list = graph.get_out_edge(node_id)
        return list
    except ValueError:
        return f'节点{node_id}不存在'
    
    except Exception as e:
        return f'返回边列表失败，原因:{e}'