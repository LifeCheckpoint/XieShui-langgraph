from pydantic import BaseModel, Field
from langchain_core.tools import tool
import json

class GraphManagerSchema(BaseModel):
    """
    当你需要对知识图谱进行管理、操作、查询或分析时，使用此工具。
    它会调用一个专门的知识图谱管理 Agent 来执行复杂的图谱任务。
    注意，下达任务时，禁止一次性下达可能造成过多知识构建的指令，导致 Agent 负载过大

    Example:

    1. 用户要求创建一个新的知识图谱来记录“人工智能”领域的知识
    - task_book:
        # 图谱创建任务书
        1. 你将要向现有的知识图谱中添加一个知识，这个知识点的具体内容和可能的关联如下:
            …(有关这个知识点的详细背景知识)
        2. 如果已经有了相关的知识，请进行检索比对，然后更新图谱，接下来…
        ……

    2. 用户要求查询现有图谱中关于“机器学习”的信息
    - task_book:
        # 图谱查询任务书
        1. 在所有可能的图谱中，查询所有与 `机器学习` 标签相关的节点，并返回它们的详细信息
        2. 注意查询时应对所有图谱都进行检索，并且采用不同的检索策略
        3. 如果没有，可以将查询范围扩大到…
        ……
    """
    task_book: str = Field(description="一份详细的任务书，描述了需要对知识图谱执行的管理任务。请尽可能详细地描述任务目标、可能的图谱相关操作等。")

@tool("graph_manager", args_schema=GraphManagerSchema)
def graph_manager(task_book: str) -> str:
    return json.dumps({
        "task_book": task_book
    }, ensure_ascii=False, indent=4)