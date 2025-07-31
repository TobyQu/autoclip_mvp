#!/usr/bin/env python3
"""
测试第7步：解说文稿生成功能
"""
import sys
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.pipeline.step7_script import run_step7_script
from src.config import get_prompt_files

def test_step7():
    """测试第7步功能"""
    print("🧪 开始测试第7步：解说文稿生成")
    
    # 检查是否存在step4_titles.json文件
    metadata_dir = Path("output/metadata")
    step4_file = metadata_dir / "step4_titles.json"
    
    if not step4_file.exists():
        print("❌ 未找到step4_titles.json文件，请先运行前6步")
        return False
    
    try:
        # 获取prompt文件配置
        prompt_files = get_prompt_files("content_review")
        
        # 运行第7步
        result = run_step7_script(
            step4_file,
            output_path=metadata_dir / "step7_scripts.json",
            metadata_dir=str(metadata_dir),
            prompt_files=prompt_files
        )
        
        print(f"✅ 第7步测试成功！生成了 {len(result)} 个解说文稿")
        
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
        
        return True
        
    except Exception as e:
        print(f"❌ 第7步测试失败: {e}")
        return False

if __name__ == "__main__":
    test_step7() 