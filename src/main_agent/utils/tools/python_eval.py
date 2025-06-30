from pydantic import BaseModel, Field
from langchain_core.tools import tool

class PythonEvalSchema(BaseModel):
    """
    Python 代码执行工具，用于执行 Python 代码片段并返回结果
    通过 eval() 函数执行
    注意，只有在确保代码片段安全，并且经过用户明确同意的情况下才能使用此工具
    """
    code: str = Field(description="Python 代码片段，不要携带额外信息防止解析错误")

@tool("python_eval", args_schema=PythonEvalSchema)
def python_eval(code: str) -> str:
    success = False
    try:
        result = eval(code)
        success = True
    except Exception as e:
        result = str(e)
    
    if success:
        return "{eval_status: Success, result: " + str(result) + "}"
    else:
        return "{eval_status: Failed, exception: " + result + "}"
