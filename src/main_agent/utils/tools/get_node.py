from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class GetNodeSchema(BaseModel):
    node_id:str = Field(description='')
    
@tool('_get_node',args_schema=GetNodeSchema)
def _get_node(node_id:str):
    graph = Knowledge_Graph()
    
    return graph.get_node(node_id)
