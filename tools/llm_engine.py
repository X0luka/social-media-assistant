import os
import json
from typing import Optional, Any, List, Dict
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class MockLLM:
    """模拟 LLM 类，用于测试时返回模拟响应"""
    
    def __init__(self, model: str = "mock-deepseek", temperature: float = 0.7):
        self.model = model
        self.temperature = temperature
    
    def invoke(self, messages: List[Dict[str, str]]) -> Any:
        """返回模拟响应"""
        # 从消息中提取内容，生成模拟响应
        user_message = ""
        for msg in messages:
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 根据任务类型生成不同的模拟响应
        if "简报" in user_message or "brief" in user_message.lower():
            mock_content = """## 🔥 AI 热点简报

### ChatGPT-4
- **用途**: 多模态 AI 对话助手
- **亮点**: 支持文本、图像、代码生成
- **评价**: 用户反馈积极，行业认可度高

### Claude 3
- **用途**: 企业级 AI 助手
- **亮点**: 安全性强，适合企业应用
- **评价**: 在隐私保护方面表现突出

**总结**: AI 工具正在向多模态和企业级应用方向发展

*注：这是模拟数据，请设置 DEEPSEEK_API_KEY 获取真实结果*"""
        elif "CV" in user_message or "计算机视觉" in user_message:
            mock_content = """## 🎯 CV 项目/趋势分析

### 技术栈
- **模型**: YOLOv8, ResNet-50
- **引擎**: TensorRT, ONNX Runtime
- **框架**: PyTorch, TensorFlow
- **其他工具**: OpenCV, CUDA

### 落地场景
基于搜索结果中的实际案例，主要应用于：
- 自动驾驶中的目标检测
- 工业质检中的缺陷识别
- 医疗影像分析

### 技术特点
- 实时推理性能优异
- 支持边缘设备部署
- 模型压缩技术成熟

**数据来源**: 所有信息均基于搜索结果，无脑补内容

*注：这是模拟数据，请设置 DEEPSEEK_API_KEY 获取真实结果*"""
        else:
            mock_content = f"""这是模拟 LLM 响应。

输入内容摘要: {user_message[:100]}...

*注：这是模拟数据，请设置 DEEPSEEK_API_KEY 获取真实结果*"""
        
        # 创建一个类似 ChatOpenAI 响应的对象
        class MockResponse:
            def __init__(self, content: str):
                self.content = content
        
        return MockResponse(mock_content)


def get_llm(
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    api_key: Optional[str] = None,
    use_mock: bool = False
) -> Any:
    """
    获取 DeepSeek-V3 LLM 实例或模拟 LLM
    
    Args:
        model: 模型名称，默认为 deepseek-chat（DeepSeek-V3）
        temperature: 温度参数，控制输出的随机性
        api_key: API Key，如果不提供则从环境变量读取
        use_mock: 如果为 True，返回模拟 LLM（用于测试）
    
    Returns:
        ChatOpenAI 实例或 MockLLM 实例
    """
    # #region agent log
    try:
        with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"llm-check","hypothesisId":"B","location":"tools/llm_engine.py:45","message":"Checking DEEPSEEK_API_KEY","data":{"use_mock":use_mock},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    if use_mock:
        # #region agent log
        try:
            with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"llm-check","hypothesisId":"B","location":"tools/llm_engine.py:50","message":"Using mock LLM","data":{"model":model},"timestamp":int(__import__('time').time()*1000)}) + '\n')
        except: pass
        # #endregion
        return MockLLM(model=model, temperature=temperature)
    
    api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
    
    # #region agent log
    try:
        with open('/workspaces/social-media-assistant/.cursor/debug.log', 'a') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"llm-check","hypothesisId":"B","location":"tools/llm_engine.py:60","message":"API key check result","data":{"has_key":bool(api_key)},"timestamp":int(__import__('time').time()*1000)}) + '\n')
    except: pass
    # #endregion
    
    if not api_key:
        raise ValueError(
            "DEEPSEEK_API_KEY 未设置。请在 .env 文件中设置 DEEPSEEK_API_KEY，"
            "或通过参数传入 api_key，或使用 use_mock=True 进行测试"
        )
    
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url="https://api.deepseek.com",
        temperature=temperature,
    )
