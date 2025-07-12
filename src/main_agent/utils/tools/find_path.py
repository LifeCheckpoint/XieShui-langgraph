from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class FindPathSchema(BaseModel):
    start_node_id: str = Field(description='')
    goal_node_id: str = Field(description='')
    
@tool('_find_path',args_schema=FindPathSchema)
def _find_path(start_node_id: str, goal_node_id: str):
    graph = Knowledge_Graph()
    
    try:
        list = graph.find_path(start_node_id,goal_node_id)
        return list
    except ValueError:
        return f'起始或终止节点不存在'
    
    except Exception as e:
        return f'返回节点列表失败，原因:{e}'