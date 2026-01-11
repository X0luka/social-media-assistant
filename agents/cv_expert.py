"""
CV Expert - 计算机视觉项目/趋势分析专家
搜索特定 CV 项目/趋势，严谨提取技术栈，分析落地场景，禁止脑补
"""
from core.state import AgentState
from tools.search import search_content
from tools.llm_engine import get_llm


def cv_generate_node(state: AgentState) -> AgentState:
    """
    生成 CV 项目/趋势分析报告
    
    Args:
        state: AgentState 状态对象，包含 input_query（CV 项目/趋势关键词）
    
    Returns:
        更新后的 AgentState，包含生成的分析报告
    """
    input_query = state.get("input_query", "").strip()
    
    if not input_query:
        raise ValueError("input_query 不能为空，请提供 CV 项目或趋势关键词")
    
    try:
        # 搜索特定 CV 项目/趋势
        # 如果缺少 API key，使用模拟数据（仅用于测试）
        import os
        use_mock_search = not bool(os.getenv("TAVILY_API_KEY"))
        use_mock_llm = not bool(os.getenv("DEEPSEEK_API_KEY"))
        search_query = f"computer vision {input_query} project technology stack"
        search_results = search_content(search_query, max_results=5, use_mock=use_mock_search)
        
        # 获取 LLM 实例（如果缺少 API key，使用模拟 LLM）
        llm = get_llm(temperature=0.5, use_mock=use_mock_llm)  # 使用较低温度以确保严谨性
        
        # 构建 System Prompt
        system_prompt = """你是一位严谨的计算机视觉专家，擅长从搜索结果中提取技术信息并进行分析。

重要原则：
1. **禁止脑补**：所有信息必须基于搜索结果，不得添加搜索结果中没有的内容
2. **严谨提取**：技术栈必须准确，包括模型名称、引擎、框架等
3. **基于事实**：落地场景分析必须基于搜索结果中的实际案例

你的任务：
1. 从搜索结果中严谨提取技术栈（模型、引擎、框架）
2. 分析项目的落地场景（必须基于搜索结果中的实际案例）
3. 总结技术特点和创新点

输出格式要求：
## 🎯 CV 项目/趋势分析

### 技术栈
- **模型**: [从搜索结果中提取的模型名称]
- **引擎**: [从搜索结果中提取的引擎名称]
- **框架**: [从搜索结果中提取的框架名称]
- **其他工具**: [其他相关技术]

### 落地场景
[基于搜索结果中的实际案例，分析应用场景]

### 技术特点
[基于搜索结果总结的技术特点和创新点]

**数据来源**: 所有信息均基于搜索结果，无脑补内容"""
        
        # 构建用户提示
        user_prompt = f"""请基于以下搜索结果，对 CV 项目/趋势 '{input_query}' 进行严谨分析：

搜索结果：
{search_results}

重要：请严格遵守"禁止脑补"原则，所有信息必须基于搜索结果。如果搜索结果中没有相关信息，请明确标注"搜索结果中未找到相关信息"。"""
        
        # 调用 LLM 生成分析报告
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "content": content,
            "steps": [f"步骤: cv_generate - 已生成 CV 项目分析报告（查询: {input_query}）"]
        }
        
    except Exception as e:
        error_msg = f"生成 CV 分析报告失败: {str(e)}"
        raise RuntimeError(f"步骤: cv_generate - {error_msg}") from e
