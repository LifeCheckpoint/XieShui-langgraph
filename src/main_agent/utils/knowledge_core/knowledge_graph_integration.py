from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Tuple
from collections import deque
import networkx as nx
import json

from src.main_agent.utils.knowledge_core.node_edge import Knowledge_Node, Knowledge_Edge
from src.main_agent.utils.knowledge_core.knowledge_graph import Knowledge_Graph

