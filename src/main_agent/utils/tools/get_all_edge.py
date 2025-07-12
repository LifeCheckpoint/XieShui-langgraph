from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from collections import deque
import uuid
from langchain_core.tools import tool
from node_class import Knowledge_Node,Knowledge_Edge,Knowledge_Graph

class GetAllEdgeSchema(BaseModel):
    pass

@tool('_get_all_edge',args_schema=GetAllEdgeSchema)
def _get_all_edge():
    graph = Knowledge_Graph()
    return graph.get_all_edge