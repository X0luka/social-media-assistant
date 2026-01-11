#!/usr/bin/env python3
"""
Social Media Assistant 主入口脚本
支持通过命令行参数启动不同类型的任务
"""
import argparse
from core.graph import graph
from core.state import AgentState


def initialize_state(
    task_type: str,
    input_query: str
) -> AgentState:
    """
    初始化 AgentState
    
    Args:
        task_type: 任务类型 (brief/cv/paper)
        input_query: 输入查询字符串
    
    Returns:
        初始化后的 AgentState
    """
    if task_type not in ["brief", "cv", "paper"]:
        raise ValueError(f"无效的任务类型: {task_type}。必须是 brief、cv 或 paper")
    
    return AgentState(
        task_type=task_type,
        input_query=input_query,
        content="",
        image_url="",
        critique="",
        iteration=0,
        steps=[]
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Social Media Assistant - 社交媒体内容生成助手"
    )
    parser.add_argument(
        "--type",
        type=str,
        required=True,
        choices=["brief", "paper", "cv"],
        help="任务类型: brief (简报), paper (论文), cv (简历)"
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="输入查询字符串（例如: AI 工具名称、CV 项目关键词等）"
    )
    
    args = parser.parse_args()
    
    # 初始化状态
    initial_state = initialize_state(
        task_type=args.type,
        input_query=args.input
    )
    
    print(f"🚀 启动任务: {args.type}")
    print(f"📝 输入查询: {args.input}")
    print("-" * 50)
    
    # 运行工作流
    try:
        final_state = graph.invoke(initial_state)
        
        print("\n✅ 任务完成！")
        print("-" * 50)
        print(f"📄 生成的内容:\n{final_state.get('content', 'N/A')}")
        print(f"\n🖼️  图片链接: {final_state.get('image_url', 'N/A')}")
        print(f"\n🔄 迭代次数: {final_state.get('iteration', 0)}")
        print(f"\n📋 执行步骤:")
        for step in final_state.get('steps', []):
            print(f"  - {step}")
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        raise


if __name__ == "__main__":
    main()
