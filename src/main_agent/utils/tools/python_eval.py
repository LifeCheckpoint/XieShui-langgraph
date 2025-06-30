from pydantic import BaseModel, Field
from langchain_core.tools import tool

class PythonEvalSchema(BaseModel):
    """
    Python 代码执行工具，用于执行 Python 代码片段并返回结果
    通过 exec() 函数执行
    需要注意以下要点：
    1. 只有在确保代码片段安全，并且经过用户明确同意的情况下才能使用此工具
    2. 你需要将结果储存到 result 变量中，由于是 exec 执行，注意不要造成副作用
    """
    code: str = Field(description="Python 代码片段，不要携带额外信息防止解析错误")

@tool("python_eval", args_schema=PythonEvalSchema)
def python_eval(code: str) -> str:
    success = False

    try:
        exec_locals = {}
        exec(code, locals=exec_locals)

        if exec_locals.get('result') is None:
            raise ValueError("执行的代码没有定义 result 变量，请确保代码中有 result 变量来存储结果")

        try:
            result = str(exec_locals.get('result'))
        except Exception as e:
            raise ValueError(f"无法将 result 转换为字符串: {e}")

        success = True

    except Exception as e:
        result = str(e)
    
    if success:
        return "python_eval 返回结果如下，请根据具体内容继续执行或回答用户：\n{eval_status: Success, result: " + result + "}"
    else:
        return "python_eval 返回结果如下，请根据具体内容继续执行或回答用户：\n{eval_status: Failed, exception: " + result + "}"
