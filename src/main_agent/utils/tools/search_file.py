from pydantic import BaseModel, Field
from langchain_core.tools import tool
from everytools import Search, SortType

class SearchFileSchema(BaseModel):
    """
    强大的文件搜索工具，基于everything的搜索功能
    """
    query_string: str = Field(description="搜索关键词或模式，例如 '*.txt' 或 'report'。请注意，在不确定具体文件吗的情况下，尽可能使用通配符拓展搜索，例如 must \"some str\" !notHas aaaor|bbbor ")
    match_case: bool = Field(default=False, description="是否区分大小写。")
    sort_type: str = Field(default="NAME_ASCENDING", description="搜索结果的排序方式，可以为NAME、PATH、SIZE、EXTENSION、DATE_CREATED、DATE_MODIFIED、ATTRIBUTES、DATE_RECENTLY_CHANGED、DATE_ACCESSED等属性的升降序（ASCENDING、DESCENDING）。例如：NAME_ASCENDING、SIZE_DESCENDING等。")
    max_results: int = Field(default=20, description="返回的最大结果数量。")

@tool("search_file", args_schema=SearchFileSchema)
def search_file(
    query_string: str,
    match_case: bool = False,
    sort_type: str = "NAME_ASCENDING",
    max_results: int = 20,
) -> str:
    try:
        # 创建带参数的搜索
        search = Search(
            query_string=query_string,
            match_case=match_case,
            sort_type=SortType.__members__.get(sort_type, SortType.NAME_ASCENDING),
            max_results=max_results,
        )
        search.execute()
        results = search.get_results()

        if not results:
            return f"未找到与条件匹配的文件。请尝试**更换搜索关键词模式为更通用的形式（如通配符）**，或者**放宽搜索条件**。"

        result_text = f"共查找到 {len(results)} 个文件:\n"
        for result in results:
            result_text += f"- {result.to_dict()}\n"

        return result_text.strip()

    except Exception as e:
        return f"搜索文件时发生错误: {e}\n请确保Everything已正确安装并运行，或者检查搜索参数是否正确。"