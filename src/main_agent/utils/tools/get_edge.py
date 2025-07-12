from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class GetEdgeSchema(BaseModel):
    edge_id:str = Field(description='')
    
    
@tool('_get_edge',args_schema=GetEdgeSchema)
def _get_edge(edge_id:str):
    graph = Knowledge_Graph()
    
    return graph.get_edge(edge_id)