"""
工作流图编排
实现 generate -> review -> [condition] -> refine -> visualize 的闭环
隔离 paper_agent，防止程序崩溃
"""
from typing import Literal
from langgraph.graph import StateGraph, END
from core.state import AgentState
from agents.brief_agent import brief_generate_node
from agents.cv_expert import cv_generate_node
from agents.reviewer import reviewer_node
from tools.image_gen import generate_image


def route_task(state: AgentState) -> AgentState:
    """
    路由节点：根据 task_type 分流到不同的工作流
    
    Args:
        state: AgentState 状态对象
    
    Returns:
        更新后的 AgentState（添加路由步骤日志）
    """
    task_type = state.get("task_type", "").lower()
    
    if task_type not in ["brief", "cv", "paper"]:
        raise ValueError(f"未知的任务类型: {task_type}。必须是 brief、cv 或 paper")
    
    # 由于 steps 使用 Annotated[List[str], add]，返回列表会自动合并
    return {
        "steps": [f"步骤: route - 任务类型: {task_type}"]
    }


def generate_node(state: AgentState) -> AgentState:
    """
    生成节点：根据 task_type 调用不同的 Agent 生成内容
    
    Args:
        state: AgentState 状态对象
    
    Returns:
        更新后的 AgentState，包含生成的内容
    """
    task_type = state.get("task_type", "").lower()
    
    if task_type == "brief":
        return brief_generate_node(state)
    elif task_type == "cv":
        return cv_generate_node(state)
    elif task_type == "paper":
        # 隔离 paper_agent，暂时返回错误提示
        return {
            "content": "Paper Agent 暂未启用，请使用 brief 或 cv 任务类型",
            "steps": ["步骤: generate - Paper Agent 暂未启用"]
        }
    else:
        raise ValueError(f"不支持的任务类型: {task_type}")


def refine_node(state: AgentState) -> AgentState:
    """
    优化节点：根据审查意见优化内容
    
    Args:
        state: AgentState 状态对象，包含 content 和 critique
    
    Returns:
        更新后的 AgentState，包含优化后的内容
    """
    content = state.get("content", "")
    critique = state.get("critique", "")
    task_type = state.get("task_type", "").lower()
    
    if not critique or critique.strip().upper() == "PASS":
        # 如果没有审查意见或已通过，直接返回
        return {
            "steps": ["步骤: refine - 无需优化"]
        }
    
    # 获取 LLM 实例（如果缺少 API key，使用模拟 LLM）
    import os
    from tools.llm_engine import get_llm
    use_mock_llm = not bool(os.getenv("DEEPSEEK_API_KEY"))
    llm = get_llm(temperature=0.7, use_mock=use_mock_llm)
    
    # 构建 System Prompt
    system_prompt = """你是一位专业的内容优化专家，擅长根据审查意见优化内容。

你的任务：
1. 仔细阅读原始内容和审查意见
2. 根据审查意见进行针对性修正
3. 确保修正后的内容专业、准确、无 AI 幻觉
4. 保持内容的吸引力和可读性"""
    
    # 构建用户提示
    user_prompt = f"""请根据以下审查意见优化内容：

原始内容：
{content}

审查意见：
{critique}

请确保修正后的内容完全符合审查意见的要求。"""
    
    try:
        # 调用 LLM 优化内容
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        refined_content = response.content if hasattr(response, 'content') else str(response)
        
        # 由于 iteration 使用 Annotated[int, add]，返回 1 会自动与当前值相加
        return {
            "content": refined_content,
            "iteration": 1,
            "steps": [f"步骤: refine - 已根据审查意见优化内容（任务类型: {task_type}）"]
        }
        
    except Exception as e:
        error_msg = f"优化内容失败: {str(e)}"
        raise RuntimeError(f"步骤: refine - {error_msg}") from e


def visualize_node(state: AgentState) -> AgentState:
    """
    可视化节点：根据内容生成配图
    
    Args:
        state: AgentState 状态对象，包含 content
    
    Returns:
        更新后的 AgentState，包含生成的图片 URL
    """
    content = state.get("content", "")
    task_type = state.get("task_type", "").lower()
    
    if not content:
        raise ValueError("content 为空，无法生成配图")
    
    try:
        # 构建图片生成提示词
        # 从内容中提取关键信息，生成科技感配图描述
        image_prompt = f"Create a modern, tech-savvy, professional illustration for {task_type} content. "
        image_prompt += "Style: futuristic, clean, minimalist, with vibrant colors. "
        image_prompt += "Theme: technology, innovation, digital transformation. "
        image_prompt += "Aspect ratio: 4:3, high quality, professional design."
        
        # 调用图片生成工具
        image_url = generate_image(
            prompt=image_prompt,
            model="fal-ai/flux/schnell",
            aspect_ratio="4:3"
        )
        
        return {
            "image_url": image_url,
            "steps": [f"步骤: visualize - 已生成配图（任务类型: {task_type}）"]
        }
        
    except Exception as e:
        error_msg = f"生成配图失败: {str(e)}"
        raise RuntimeError(f"步骤: visualize - {error_msg}") from e


def should_continue(state: AgentState) -> Literal["refine", "visualize"]:
    """
    判断是否继续优化或进入可视化
    
    Args:
        state: AgentState 状态对象
    
    Returns:
        "refine" 继续优化, "visualize" 进入可视化
    """
    critique = state.get("critique", "")
    iteration = state.get("iteration", 0)
    
    # 如果审查结果为 'PASS'（精确匹配）或 iteration >= 2，进入可视化
    if critique and critique.strip() == "PASS":
        return "visualize"
    elif iteration >= 2:
        return "visualize"
    else:
        # 否则继续优化
        return "refine"


def create_graph() -> StateGraph:
    """
    创建并配置工作流图
    
    Returns:
        配置好的 StateGraph 实例
    """
    # 创建状态图
    workflow = StateGraph(AgentState)
    
    # 添加节点
    workflow.add_node("route", route_task)
    workflow.add_node("generate", generate_node)
    workflow.add_node("review", reviewer_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("visualize", visualize_node)
    
    # 设置入口点
    workflow.set_entry_point("route")
    
    # 配置路由：根据 task_type 分流
    workflow.add_conditional_edges(
        "route",
        lambda state: state.get("task_type", "").lower(),
        {
            "brief": "generate",
            "cv": "generate",
            "paper": "generate",  # 虽然暂未启用，但保持路由完整性
        }
    )
    
    # 工作流：generate -> review -> [condition] -> refine -> visualize
    workflow.add_edge("generate", "review")
    workflow.add_conditional_edges(
        "review",
        should_continue,
        {
            "refine": "refine",
            "visualize": "visualize"
        }
    )
    workflow.add_edge("refine", "review")  # 优化后重新审查
    workflow.add_edge("visualize", END)
    
    return workflow.compile()


# 导出编译好的图
graph = create_graph()
