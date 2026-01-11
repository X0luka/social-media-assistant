from typing import TypedDict, Optional


class AgentState(TypedDict):
    """Agent 状态定义"""
    task_type: str  # 任务类型
    content: str  # 内容
    iteration: int  # 迭代次数
    critique: Optional[str]  # 批评/反馈
