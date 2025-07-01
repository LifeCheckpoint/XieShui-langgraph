from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool

class AskQuestionSchema(BaseModel):
    """
    当你需要向用户确认信息的时候，使用此工具向用户提问。
    对于问题，应该提供一系列选项供用户选择，包含2-5个建议答案，这些答案按照优先级或逻辑顺序从问题引出。
    
    Examples:

    1. 向用户确认其指令中模糊的部分，要求提供具体信息
    - question: 您在任务描述中提到的“数据分析”具体指什么？
    - option_1: 数据清洗，将原始数据转换为可用格式
    - option_2: 数据可视化，生成图表和图形可供分析
    - option_3: 统计分析，计算平均值、标准差等
    - option_4: 机器学习，使用算法进行预测和分类，并生成模型

    2. 向用户确认是否执行某些操作
    - question: 您是否认同我的分析并开始执行？
    - option_1: 是的，我同意并希望开始执行
    - option_2: 不，我需要更多信息
    - option_3: 你的分析正确，但我希望你再考虑一下执行的方式
    """
    question: str = Field(description="需要向用户提问的问题，这应该是一个明确、具体的问题，可以解决您需要的信息")
    option_1: str = Field(description="选项1的内容")
    option_2: str = Field(description="选项2的内容")
    option_3: Optional[str] = Field(default=None, description="选项3的内容（可选）")
    option_4: Optional[str] = Field(default=None, description="选项4的内容（可选）")
    option_5: Optional[str] = Field(default=None, description="选项5的内容（可选）")

@tool("ask_question", args_schema=AskQuestionSchema)
def ask_question(
    question: str,
    option_1: str,
    option_2: str,
    option_3: Optional[str] = None,
    option_4: Optional[str] = None,
    option_5: Optional[str] = None
) -> str:
    options = [option_1, option_2]
    if option_3:
        options.append(option_3)
    if option_4:
        options.append(option_4)
    if option_5:
        options.append(option_5)

    return f"榭水有一个问题: {question}\n\n" + "\n".join(f"- {opt}" for opt in options)
