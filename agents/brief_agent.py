"""
Brief Agent - AI 行业热点简报生成器
搜索 AI 行业 24h 热点，提取工具名、用途、评价，输出社交媒体简报
"""
from core.state import AgentState
from tools.search import search_content
from tools.llm_engine import get_llm


def brief_generate_node(state: AgentState) -> AgentState:
    """
    生成 AI 行业热点简报
    
    Args:
        state: AgentState 状态对象，包含 input_query
    
    Returns:
        更新后的 AgentState，包含生成的简报内容
    """
    input_query = state.get("input_query", "").strip()
    
    if not input_query:
        # 如果没有输入查询，使用默认的 AI 行业热点搜索
        search_query = "AI industry news latest 24 hours tools"
    else:
        search_query = f"AI industry {input_query} latest 24 hours tools"
    
    try:
        # 搜索 AI 行业 24h 热点
        # 如果缺少 API key，使用模拟数据（仅用于测试）
        import os
        use_mock_search = not bool(os.getenv("TAVILY_API_KEY"))
        use_mock_llm = not bool(os.getenv("DEEPSEEK_API_KEY"))
        search_results = search_content(search_query, max_results=5, use_mock=use_mock_search)
        
        # 获取 LLM 实例（如果缺少 API key，使用模拟 LLM）
        llm = get_llm(temperature=0.7, use_mock=use_mock_llm)
        
        # 构建 System Prompt
        system_prompt = """你是一位专业的 AI 行业分析师，擅长从搜索结果中提取关键信息并生成社交媒体简报。

你的任务：
1. 从搜索结果中提取 AI 工具/产品的名称
2. 总结每个工具的用途和功能
3. 提取用户评价或行业反馈
4. 生成适合社交媒体发布的简报（简洁、有趣、专业）

输出格式要求：
## 🔥 AI 热点简报

### [工具/产品名称 1]
- **用途**: [简要描述]
- **亮点**: [关键特性或优势]
- **评价**: [用户反馈或行业观点]

### [工具/产品名称 2]
...

**总结**: [一句话总结今日 AI 行业趋势]"""
        
        # 构建用户提示
        user_prompt = f"""请基于以下搜索结果，生成一份 AI 行业热点简报：

搜索结果：
{search_results}

请严格按照输出格式要求，提取工具名、用途、评价，并生成社交媒体简报。"""
        
        # 调用 LLM 生成简报
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "content": content,
            "steps": [f"步骤: brief_generate - 已生成 AI 行业热点简报（搜索: {search_query}）"]
        }
        
    except Exception as e:
        error_msg = f"生成简报失败: {str(e)}"
        raise RuntimeError(f"步骤: brief_generate - {error_msg}") from e
