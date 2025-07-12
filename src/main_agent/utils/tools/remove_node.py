from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class RemoveNodeSchema(BaseModel):
    node_id:str = Field(description='')
    
@tool('_remove_node',args_schema=RemoveNodeSchema)
def _remove_node(node_id:str):
    graph = Knowledge_Graph()
    
    try:
        graph.remove_node(node_id)
    except ValueError:
        return f'节点{node_id}不存在'
    
    except Exception as e:
        return f'删除节点失败，原因:{e}'