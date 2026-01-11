"""
通用 Reviewer 节点
作为严谨的编辑，检查 Agent 输出的内容质量
"""
from core.state import AgentState
from tools.llm_engine import get_llm


def reviewer_node(state: AgentState) -> AgentState:
    """
    审查生成的内容
    
    Args:
        state: AgentState 状态对象，包含 content（生成的内容）
    
    Returns:
        更新后的 AgentState，包含 critique（审查意见，如果通过则为 'PASS'）
    """
    content = state.get("content", "")
    task_type = state.get("task_type", "").lower()
    
    if not content:
        raise ValueError("content 为空，请先执行生成节点")
    
    # 获取 LLM 实例（如果缺少 API key，使用模拟 LLM）
    import os
    use_mock_llm = not bool(os.getenv("DEEPSEEK_API_KEY"))
    llm = get_llm(temperature=0.3, use_mock=use_mock_llm)
    
    # 构建 System Prompt
    system_prompt = """你是一位严谨的编辑，负责审查社交媒体内容的质量。

你的审查准则：
1. **内容专业性**：检查内容是否专业、准确，是否符合行业标准
2. **AI 幻觉检测**：检查是否存在 AI 幻觉（虚假信息、不实描述、过度夸大）
3. **配图描述**：检查配图描述是否足够酷、吸引人，是否与内容匹配

输出规范：
- 如果内容完全合格，请只输出：PASS
- 如果内容不合格，请输出具体的修改意见，格式如下：

修改意见：
1. [具体问题1及修改建议]
2. [具体问题2及修改建议]
3. [具体问题3及修改建议]
...

请严格审查，确保内容质量。"""
    
    # 根据任务类型构建不同的用户提示
    if task_type == "brief":
        task_context = "这是一份 AI 行业热点简报"
    elif task_type == "cv":
        task_context = "这是一份 CV 项目/趋势分析报告"
    else:
        task_context = "这是一份生成的内容"
    
    user_prompt = f"""请审查以下{task_context}：

{content}

请严格按照审查准则进行检查，特别关注：
1. 内容是否专业、准确
2. 是否存在 AI 幻觉（虚假信息、不实描述）
3. 配图描述是否足够酷、吸引人

给出审查结果。"""
    
    try:
        # 调用 LLM 进行审查
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        critique = response.content if hasattr(response, 'content') else str(response)
        
        # 清理输出，确保 PASS 是精确匹配
        critique_clean = critique.strip()
        
        # 判断是否通过
        is_pass = critique_clean.upper() == "PASS"
        
        return {
            "critique": critique_clean,
            "steps": [f"步骤: reviewer - 审查结果: {'通过' if is_pass else '需要修改'}"]
        }
        
    except Exception as e:
        error_msg = f"审查失败: {str(e)}"
        raise RuntimeError(f"步骤: reviewer - {error_msg}") from e
