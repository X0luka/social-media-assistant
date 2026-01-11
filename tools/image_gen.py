"""
fal.ai 图片生成工具
使用 flux/schnell 模型生成科技感配图
"""
import os
from typing import Optional
from fal_client import run
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def generate_image(
    prompt: str,
    model: str = "fal-ai/flux/schnell",
    aspect_ratio: str = "4:3"
) -> str:
    """
    使用 fal.ai 生成图片
    
    Args:
        prompt: 图片生成提示词
        model: 模型名称，默认为 flux/schnell
        aspect_ratio: 图片比例，默认为 4:3
    
    Returns:
        生成的图片 URL
    """
    api_key = os.getenv("FAL_KEY")
    
    if not api_key:
        raise ValueError(
            "FAL_KEY 未设置。请在 .env 文件中设置 FAL_KEY"
        )
    
    try:
        # fal_client 会自动从环境变量 FAL_KEY 读取 API key
        # 确保环境变量已设置
        os.environ["FAL_KEY"] = api_key
        
        # 调用模型生成图片
        # 使用 run() 同步调用
        result = run(
            model,
            arguments={
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "num_images": 1,
            }
        )
        
        # 提取图片 URL
        # fal.ai 返回格式可能是 {"images": [{"url": "..."}]} 或直接返回 URL
        if isinstance(result, dict):
            images = result.get("images", [])
            if images and len(images) > 0:
                image_data = images[0]
                if isinstance(image_data, dict):
                    image_url = image_data.get("url", "")
                else:
                    image_url = str(image_data)
                if image_url:
                    return image_url
            # 如果直接返回 URL
            if "url" in result:
                return result["url"]
        
        # 如果 result 是字符串，直接返回
        if isinstance(result, str):
            return result
        
        raise ValueError("生成图片失败：未返回有效的图片 URL")
        
    except Exception as e:
        error_msg = f"fal.ai 图片生成失败: {str(e)}"
        raise RuntimeError(error_msg) from e
