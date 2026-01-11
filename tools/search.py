"""
Tavily 搜索工具
用于搜索和获取网页内容摘要
"""
import os
import json
from typing import List, Dict, Any
from tavily import TavilyClient
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def search_content(query: str, max_results: int = 5, use_mock: bool = False) -> str:
    """
    使用 Tavily 搜索内容并返回清洗后的网页文本摘要
    
    Args:
        query: 搜索查询字符串
        max_results: 最大返回结果数量，默认 5
        use_mock: 如果为 True，在缺少 API key 时使用模拟数据
    
    Returns:
        清洗后的网页文本摘要字符串
    """
    # #region agent log
    try:
        with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"api-check","hypothesisId":"A","location":"tools/search.py:30","message":"Checking TAVILY_API_KEY","data":{"query":query,"use_mock":use_mock},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    api_key = os.getenv("TAVILY_API_KEY")
    
    # #region agent log
    try:
        with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"api-check","hypothesisId":"A","location":"tools/search.py:35","message":"API key check result","data":{"has_key":bool(api_key),"use_mock":use_mock},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    if not api_key:
        if use_mock:
            # #region agent log
            try:
                with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"api-check","hypothesisId":"A","location":"tools/search.py:40","message":"Using mock data","data":{"query":query},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            # 返回模拟数据用于测试
            return f"""[1] AI Industry News - {query}
来源: https://example.com/ai-news
摘要: This is a mock search result for testing purposes. The query was: {query}. In a real scenario, this would contain actual search results from Tavily API.

[2] Technology Trends - {query}
来源: https://example.com/tech-trends
摘要: Mock data for demonstration. Please set TAVILY_API_KEY in your .env file to get real search results."""
        raise ValueError(
            "TAVILY_API_KEY 未设置。请在 .env 文件中设置 TAVILY_API_KEY，"
            "或使用 use_mock=True 参数进行测试"
        )
    
    try:
        client = TavilyClient(api_key=api_key)
        
        # 执行搜索
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth="advanced"  # 使用高级搜索深度
        )
        
        # 提取和清洗结果
        results = response.get("results", [])
        
        if not results:
            return f"未找到与 '{query}' 相关的搜索结果。"
        
        # 构建清洗后的文本摘要
        summaries = []
        for i, result in enumerate(results, 1):
            title = result.get("title", "无标题")
            content = result.get("content", "")
            url = result.get("url", "")
            
            # 清洗内容：移除多余的空白字符
            content_clean = " ".join(content.split())
            
            summaries.append(
                f"[{i}] {title}\n"
                f"来源: {url}\n"
                f"摘要: {content_clean[:500]}..."  # 限制长度
            )
        
        return "\n\n".join(summaries)
        
    except Exception as e:
        # #region agent log
        try:
            with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"api-check","hypothesisId":"C","location":"tools/search.py:100","message":"Tavily API call failed","data":{"error":str(e),"error_type":type(e).__name__,"use_mock":use_mock},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        
        # 如果 API key 无效或请求失败，且允许使用模拟数据，则回退到模拟数据
        if use_mock or "invalid API key" in str(e).lower() or "unauthorized" in str(e).lower():
            # #region agent log
            try:
                with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"api-check","hypothesisId":"C","location":"tools/search.py:105","message":"Falling back to mock data due to API error","data":{"query":query},"timestamp":int(__import__('time').time()*1000)}) + '\n')
            except: pass
            # #endregion
            # 返回模拟数据用于测试
            return f"""[1] AI Industry News - {query}
来源: https://example.com/ai-news
摘要: This is a mock search result for testing purposes. The query was: {query}. In a real scenario, this would contain actual search results from Tavily API.

[2] Technology Trends - {query}
来源: https://example.com/tech-trends
摘要: Mock data for demonstration. Please set TAVILY_API_KEY in your .env file to get real search results."""
        
        error_msg = f"Tavily 搜索失败: {str(e)}"
        raise RuntimeError(error_msg) from e
