"""
Paper Agent 节点实现
包含论文抓取、总结和审查的核心逻辑
"""
import arxiv
from core.state import AgentState
from tools.llm_engine import get_llm


def fetch_arxiv_node(state: AgentState) -> AgentState:
    """
    从 Arxiv 抓取论文信息
    
    Args:
        state: AgentState 状态对象，包含 task_input (Arxiv ID)
    
    Returns:
        更新后的 AgentState，包含 raw_data（论文的标题、摘要、作者和 PDF 链接）
    """
    task_input = state.get("task_input", "").strip()
    
    if not task_input:
        raise ValueError("task_input 不能为空，请提供有效的 Arxiv ID")
    
    try:
        # 搜索论文（支持 Arxiv ID 格式，如 "2301.12345" 或 "arXiv:2301.12345"）
        arxiv_id = task_input.replace("arXiv:", "").replace("arxiv:", "").strip()
        
        # 使用 arxiv 库搜索论文
        search = arxiv.Search(
            id_list=[arxiv_id],
            max_results=1
        )
        
        paper = next(search.results(), None)
        
        if paper is None:
            raise ValueError(f"未找到 Arxiv ID 为 {arxiv_id} 的论文")
        
        # 提取论文信息：title, summary, authors, pdf_url
        title = paper.title
        summary = paper.summary
        authors = [author.name for author in paper.authors]
        authors_str = ", ".join(authors)
        pdf_url = paper.pdf_url
        
        # 构建原始数据字符串，包含所有必需信息
        raw_data = f"""标题: {title}

作者: {authors_str}

摘要:
{summary}

PDF 链接: {pdf_url}
"""
        
        return {
            "raw_data": raw_data,
            "steps": [f"步骤: fetch_arxiv - 成功抓取论文: {title} (ID: {arxiv_id})"]
        }
        
    except arxiv.ArxivError as e:
        error_msg = f"Arxiv API 错误: {str(e)}"
        raise RuntimeError(f"步骤: fetch_arxiv - {error_msg}") from e
    except Exception as e:
        error_msg = f"抓取 Arxiv 论文失败: {str(e)}"
        raise RuntimeError(f"步骤: fetch_arxiv - {error_msg}") from e


def pyramid_summarize_node(state: AgentState) -> AgentState:
    """
    使用金字塔原理对论文进行总结
    
    Args:
        state: AgentState 状态对象，包含 raw_data 和可选的 critique
    
    Returns:
        更新后的 AgentState，包含生成的总结内容
    """
    raw_data = state.get("raw_data", "")
    critique = state.get("critique")
    current_iteration = state.get("iteration", 0)
    
    if not raw_data:
        raise ValueError("raw_data 为空，请先执行 fetch_arxiv_node")
    
    # 获取 LLM 实例
    llm = get_llm(temperature=0.7)
    
    # 构建 System Prompt：扮演资深视觉算法专家
    system_prompt = """你是一位资深的视觉算法专家，擅长使用"金字塔原理"对学术论文进行结构化总结。

金字塔原理要求：
1. 结论先行：首先给出核心结论
2. 以上统下：用创新点支撑核心结论
3. 归类分组：清晰列出技术栈和性能指标

输出格式要求（必须包含以下四个部分）：
## 核心矛盾解决
[一句话概括论文要解决的核心矛盾或问题]

## 三大创新支柱
1. [第一个创新点]
2. [第二个创新点]
3. [第三个创新点]

## 关键性能指标
[列出论文中的关键性能指标、实验数据或对比结果]

## 技术栈列表
[列出论文使用的主要技术、方法、框架或工具]"""
    
    # 构建用户提示
    user_prompt = f"""请对以下论文进行金字塔原理总结：

{raw_data}"""
    
    # 如果 state['critique'] 中存在反馈，必须在 Prompt 中要求 Agent 根据反馈进行针对性修正
    if critique and critique.strip().upper() != "PASS":
        user_prompt += f"""

重要：请根据以下审查意见进行针对性修正：
{critique}

请确保在本次生成的总结中显式修正上述问题，避免重复相同的错误。"""
    
    try:
        # 调用 LLM 生成总结
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        response = llm.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        return {
            "content": content,
            "steps": [f"步骤: pyramid_summarize - 已生成金字塔原理总结（迭代: {current_iteration + 1}）"]
        }
        
    except Exception as e:
        error_msg = f"生成总结失败: {str(e)}"
        raise RuntimeError(f"步骤: pyramid_summarize - {error_msg}") from e


def reflection_critic_node(state: AgentState) -> AgentState:
    """
    作为冷酷的学术审稿人，审查生成的摘要
    
    Args:
        state: AgentState 状态对象，包含 content（生成的总结）和 raw_data（原始论文信息）
    
    Returns:
        更新后的 AgentState，包含 critique（审查意见，如果通过则为 'PASS'）和增加的 iteration
    """
    content = state.get("content", "")
    raw_data = state.get("raw_data", "")
    
    if not content:
        raise ValueError("content 为空，请先执行 pyramid_summarize_node")
    
    if not raw_data:
        raise ValueError("raw_data 为空，无法进行对比审查")
    
    # 获取 LLM 实例（使用较低温度以确保严谨性）
    llm = get_llm(temperature=0.3)
    
    # 构建 System Prompt：扮演冷酷的学术审稿人
    system_prompt = """你是一位冷酷的学术审稿人，以严格的标准审查论文摘要。

你的审查任务：
1. **逻辑漏洞检测**：检查总结中的逻辑是否严密，是否存在推理漏洞
2. **数据错误检测**：对比原始摘要，检查总结中的数据、数字、指标是否准确
3. **过度夸张检测**：检查总结是否存在过度夸大、不实描述或与原文不符的表述

输出规范：
- 如果摘要完全合格，请只输出：PASS
- 如果摘要不合格，请输出具体的修改意见列表，格式如下：

修改意见：
1. [具体问题1及修改建议]
2. [具体问题2及修改建议]
3. [具体问题3及修改建议]
...

请严格对比原始摘要和生成的总结，确保审查的准确性和客观性。"""
    
    # 构建用户提示：对比 raw_data 中的原始摘要和生成的 content
    user_prompt = f"""请对比以下原始论文摘要和生成的总结，进行严格审查：

原始论文摘要（来自 raw_data）：
{raw_data}

生成的总结（来自 content）：
{content}

请严格按照审查任务进行检查，对比两者的一致性，并给出审查结果。"""
    
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
        
        # 若不合格，增加 iteration 计数
        # 由于 iteration 使用 Annotated[int, add]，返回 1 会自动与当前值相加
        result = {
            "critique": critique_clean,
            "steps": [f"步骤: reflection_critic - 审查结果: {'通过' if is_pass else '需要修改'}"]
        }
        
        # 若不合格，增加 iteration 计数
        if not is_pass:
            result["iteration"] = 1
        
        return result
        
    except Exception as e:
        error_msg = f"审查失败: {str(e)}"
        raise RuntimeError(f"步骤: reflection_critic - {error_msg}") from e
