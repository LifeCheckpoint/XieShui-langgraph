from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool
import json

class DeepResearchSchema(BaseModel):
    """
    当你需要对一个话题进行深度研究时，使用此工具生成一份非常全面而详细的深度报告
    注意，由于这个过程耗时较久，你必须在**调用此工具前**使用自然语言向用户**二次确认你的调用计划**
    
    Examples:

    1. 用户要求对信息学奥赛的出题和社区进行分析，并得到用户二次确认
    - subject: 探究中国信息学竞赛的发展中，尤其是题目风格、类型、难度、知识点的变化中，非官方性质的社区交流（包括网络社区、联考等）产生的影响是怎样的。并结合其他因素，预测未来各级比赛的题目风向
    - recursion: 3

    2. 用户要求对量子机器学习中量子随机森林的研究现状进行分析，并得到用户二次确认
    - subject: 量子机器学习中量子随机森林的研究现状
    - recursion: 4
    """
    subject: str = Field(description="你将要研究的话题，清晰简明")
    recursion: str = Field(description="研究进行的轮次，一般性话题建议设置为3，专业或资料稀缺的话题建议设置为4；默认为3")

@tool("deep_research", args_schema=DeepResearchSchema)
def deep_research(subject: str, recursion: Optional[int] = 3) -> str:
    return json.dumps({
        "subject": subject,
        "recursion": recursion
    }, ensure_ascii=False, indent=4)
