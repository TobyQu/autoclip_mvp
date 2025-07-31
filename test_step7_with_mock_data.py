#!/usr/bin/env python3
"""
使用模拟数据测试第7步：解说文稿生成功能
"""
import sys
import json
import tempfile
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline.step7_script import run_step7_script
from src.config import get_prompt_files

def create_mock_step4_data():
    """创建模拟的step4_titles.json数据"""
    mock_data = [
        {
            "id": "1",
            "outline": "Snoggletog节的背景与节日氛围",
            "generated_title": "维京人与龙的节日庆典：Snoggletog节的温馨时刻",
            "content": [
                "这里是博克岛 狂风呼啸 没有阳光的气候",
                "恶劣到可以冻坏你的脾脏",
                "我们一年一度的节日",
                "我们称之为Snoggletog",
                "为什么我们会会选择这样一个愚蠢的名字仍是一个谜",
                "但随着漫长的战争的结束",
                "以及龙和我们一起生活 今年的Snoggletog节",
                "一定会成为一段难以磨灭的记忆"
            ],
            "recommend_reason": "奇幻与温情交织，描绘维京与龙共庆节日的别样浪漫，画面感十足。",
            "start_time": "00:00:14,860",
            "end_time": "00:03:22,040",
            "final_score": 0.86,
            "chunk_index": 0
        },
        {
            "id": "2",
            "outline": "龙群突然离开引发的混乱与不安",
            "generated_title": "龙群离去的震撼瞬间：维京人的情感考验",
            "content": [
                "搞什么鬼",
                "雷神搞什么鬼",
                "回来 你们干什么去",
                "Meatlug",
                "-怎么了? -发生什么事了?",
                "希卡普在哪?",
                "你觉得怎样 伙计? 想再来一次吗?"
            ],
            "recommend_reason": "悬念迭起，情感张力十足，展现维京人与龙之间深厚羁绊的动人瞬间。",
            "start_time": "00:03:22,570",
            "end_time": "00:06:15,820",
            "final_score": 0.81,
            "chunk_index": 0
        }
    ]
    return mock_data

def test_step7_with_mock():
    """使用模拟数据测试第7步功能"""
    print("🧪 开始使用模拟数据测试第7步：解说文稿生成")
    
    try:
        # 创建本地测试目录
        test_dir = Path("test_output")
        test_dir.mkdir(exist_ok=True)
        
        # 创建模拟的step4_titles.json文件
        mock_data = create_mock_step4_data()
        step4_file = test_dir / "step4_titles.json"
        
        with open(step4_file, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 创建模拟数据文件: {step4_file}")
        
        # 获取prompt文件配置
        prompt_files = get_prompt_files("content_review")
        
        # 运行第7步
        result = run_step7_script(
            step4_file,
            output_path=test_dir / "step7_scripts.json",
            metadata_dir=str(test_dir),
            prompt_files=prompt_files
        )
        
        print(f"✅ 第7步测试成功！生成了 {len(result)} 个解说文稿")
        
        # 保存结果到本地文件
        with open(test_dir / "step7_result.json", 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {test_dir / 'step7_result.json'}")
        
        # 显示第一个片段的解说文稿示例
        if result:
            first_clip = result[0]
            script = first_clip.get('script', {})
            print("\n📝 第一个片段的解说文稿示例：")
            print(f"标题: {first_clip.get('generated_title', 'N/A')}")
            print(f"开场: {script.get('opening', 'N/A')}")
            print(f"主体: {script.get('main_content', 'N/A')[:100]}...")
            print(f"结尾: {script.get('closing', 'N/A')}")
            print(f"时长: {script.get('total_duration', 'N/A')}秒")
            print(f"情感基调: {script.get('emotion_tone', 'N/A')}")
            print(f"目标受众: {script.get('target_audience', 'N/A')}")
            print(f"关键要点: {script.get('key_points', [])}")
        
        return True
        
    except Exception as e:
        print(f"❌ 第7步测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_step7_with_mock() 