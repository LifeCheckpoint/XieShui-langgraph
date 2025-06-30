from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.tools import tool

class AskQuestionSchema(BaseModel):
    """
    当你需要向用户确认信息的时候，使用此工具向用户提问
    对于问题，应该提供一系列选项供用户选择。
    例如：你可以询问用户是否需要继续执行任务，或者需要提供更多信息。
    """
    question: str = Field(description="需要向用户提问的问题")
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
