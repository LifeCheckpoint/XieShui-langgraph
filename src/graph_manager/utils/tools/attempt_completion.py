from pydantic import BaseModel, Field
from langchain_core.tools import tool
import json

class AttemptCompletionSchema(BaseModel):
    """
    当你认为知识图谱管理任务完成的时候，使用此工具向系统确认该次任务完成。收到工具使用结果并确认任务已完成后，使用此工具向用户展示您的工作结果。
    信息提供原则: **必须非常详细，包含所有你阅读图谱发现的信息**

    Example:

    1. 已经成功完成了知识图谱管理任务
    - status: 完成对“启真问智”人工智能模型&智能体大赛的知识图谱建模
    - detail: 我首先分析了现有图谱节点，发现图谱中尚未包含有关竞赛主题的节点，因此我从…开始，创建了…。在任务计划书中，经分析我认为，需要拆分…为多个节点，以便更好地组织和展示信息。接着，我创建了…等节点，并将它们与现有有关…节点连接起来，形成了完整的知识图谱。最后，我对图谱进行了验证，确保所有节点和边都正确无误。

    2. 通过图谱获取了非常详细的信息
    - status: 搜寻并成功查找到有关问题“进化是否必须通过死亡完成？”的相关信息
    - detail: 我首先从知识图谱中提取了与“进化”和“死亡”相关的节点，然后分析了这些节点之间的关系，发现有多个节点涉及到生物学和哲学领域的讨论。接着，我对这些节点进行了深入研究，提取了相关的文献和观点，并将它们整理成一份详细的报告，涵盖了不同学科对该问题的看法。报告内容如下:
        (尽可能详细的报告) 根据节点内容，我认为答案是:否。根据节点…，无论有没有死亡，生物都可以进化。无论生物体是否进行繁殖，多细胞生物的细胞可以传代、发生变异并积累变异、替换其他细胞。从节点…出发，通过关系为…的边访问了节点…，我注意到单细胞生物可以在不分裂的情况下改变基因序列…
    """
    status: str = Field(description="任务完成状态")
    detail: str = Field(description="任务完成情况描述，描述该任务通过什么方式被完成，最终结果是什么。如果是报告信息，一定要尽可能详细")

@tool("attempt_completion", args_schema=AttemptCompletionSchema)
def attempt_completion(status: str, detail: str) -> str:
    return json.dumps({
        "status": status,
        "detail": detail
    }, ensure_ascii=False, indent=4)