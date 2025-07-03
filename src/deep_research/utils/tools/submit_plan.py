from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool

class SubmitPlanSchema(BaseModel):
    """
    研究计划提交工具，如果你需要，请调用该工具以提交研究计划
    """
    research_range: str = Field(description="研究范围，描述你计划研究的（子）主题或（子）领域。例：我正在着手对量子机器学习（QML）的理论领域进行全面回顾，重点关注过去8到10年（2015-2025）的研究进展")
    research_goal: str = Field(description="研究目标，描述你计划实现的具体目标。例：我的目标是深入探讨QML算法的广度及其未来的发展方向")
    research_method: str = Field(description="研究方法概述，描述你将如何进行研究。例：我将首先从…入手，通过…，特别是针对…，来…。我计划涵盖…等。此外，我还会…。我还会收集…，最终将所有收集到的信息综合成一份全面的综述")

@tool("submit_plan", args_schema=SubmitPlanSchema)
def submit_plan(research_range: str, research_goal: str, research_method: str) -> str:
    # 注意在下一节点将该研究计划添加到 previous_info
    return f"研究计划已成功提交"
