from typing import TypedDict, List, Annotated
from operator import add


class AgentState(TypedDict):
    """Agent 状态定义 - 使用 langgraph 的 TypedDict"""
    task_type: str  # 任务类型: brief/cv/paper
    input_query: str  # 输入查询字符串
    content: str  # 生成的文案
    image_url: str  # 生成的图片链接
    critique: str  # 存储 Reviewer 的修改意见
    iteration: Annotated[int, add]  # 迭代次数，使用 operator.add 记录
    steps: Annotated[List[str], add]  # 记录每一步的日志，使用 operator.add 记录
