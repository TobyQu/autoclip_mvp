"""
Step 7: 解说文稿生成 - 为视频片段生成详细的解说文稿
"""
import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from collections import defaultdict

from ..utils.llm_client import LLMClient
from ..utils.text_processor import TextProcessor
from ..config import PROMPT_FILES, METADATA_DIR

logger = logging.getLogger(__name__)

class ScriptGenerator:
    """解说文稿生成器"""
    
    def __init__(self, metadata_dir: Optional[Path] = None, prompt_files: Dict = None):
        self.llm_client = LLMClient()
        self.text_processor = TextProcessor()
        
        # 加载提示词
        prompt_files_to_use = prompt_files if prompt_files is not None else PROMPT_FILES
        with open(prompt_files_to_use['script'], 'r', encoding='utf-8') as f:
            self.script_prompt = f.read()
        
        # 使用传入的metadata_dir或默认值
        if metadata_dir is None:
            metadata_dir = METADATA_DIR
        self.metadata_dir = metadata_dir
        self.llm_raw_output_dir = self.metadata_dir / "step7_llm_raw_output"
    
    def generate_scripts(self, clips_with_titles: List[Dict]) -> List[Dict]:
        """
        为带标题的切片生成解说文稿 (按块批量处理，并增加缓存)
        """
        if not clips_with_titles:
            return []
            
        logger.info(f"开始为 {len(clips_with_titles)} 个视频片段进行批量解说文稿生成...")
        
        self.llm_raw_output_dir.mkdir(parents=True, exist_ok=True)
        
        clips_by_chunk = defaultdict(list)
        for clip in clips_with_titles:
            clips_by_chunk[clip.get('chunk_index', 0)].append(clip)
            
        all_clips_with_scripts = []
        for chunk_index, chunk_clips in clips_by_chunk.items():
            logger.info(f"处理块 {chunk_index}，其中包含 {len(chunk_clips)} 个片段...")
            
            try:
                logger.info(f"  > 开始调用API生成解说文稿...")
                input_for_llm = [
                    {
                        "id": clip.get('id'),
                        "title": clip.get('generated_title', clip.get('outline')),
                        "content": clip.get('content'),
                        "recommend_reason": clip.get('recommend_reason'),
                        "start_time": clip.get('start_time'),
                        "end_time": clip.get('end_time'),
                        "outline": clip.get('outline')
                    } for clip in chunk_clips
                ]
                
                raw_response = self.llm_client.call_with_retry(self.script_prompt, input_for_llm)
                
                if raw_response:
                    # 保存LLM原始响应用于调试
                    llm_cache_path = self.llm_raw_output_dir / f"chunk_{chunk_index}.txt"
                    with open(llm_cache_path, 'w', encoding='utf-8') as f:
                        f.write(raw_response)
                    logger.info(f"  > LLM原始响应已保存到 {llm_cache_path}")
                    scripts_map = self.llm_client.parse_json_response(raw_response)
                else:
                    scripts_map = {}
                
                if not isinstance(scripts_map, dict):
                    logger.warning(f"  > LLM返回的解说文稿不是一个字典: {scripts_map}，使用默认解说文稿。")
                    # 为每个片段添加默认解说文稿
                    for clip in chunk_clips:
                        clip['script'] = self._generate_default_script(clip)
                    all_clips_with_scripts.extend(chunk_clips)
                    continue

                for clip in chunk_clips:
                    clip_id = clip.get('id')
                    script_data = scripts_map.get(clip_id)
                    if script_data and isinstance(script_data, dict):
                        # 验证解说文稿数据的完整性
                        required_fields = ['opening', 'main_content', 'closing', 'total_duration', 'key_points', 'emotion_tone', 'target_audience']
                        if all(field in script_data for field in required_fields):
                            clip['script'] = script_data
                            logger.info(f"  > 为片段 {clip_id} ('{clip.get('generated_title', '')[:20]}...') 生成解说文稿")
                        else:
                            logger.warning(f"  > 片段 {clip_id} 的解说文稿数据不完整，使用默认值")
                            clip['script'] = self._generate_default_script(clip)
                    else:
                        logger.warning(f"  > 未能为片段 {clip_id} 找到或解析解说文稿，使用默认值")
                        clip['script'] = self._generate_default_script(clip)
                
                all_clips_with_scripts.extend(chunk_clips)

            except Exception as e:
                logger.error(f"  > 为块 {chunk_index} 生成解说文稿时出错: {e}")
                # 为每个片段添加默认解说文稿
                for clip in chunk_clips:
                    clip['script'] = self._generate_default_script(clip)
                all_clips_with_scripts.extend(chunk_clips)
                continue
                
        logger.info("所有视频片段解说文稿生成完成")
        return all_clips_with_scripts
    
    def _generate_default_script(self, clip: Dict) -> Dict:
        """生成默认的解说文稿"""
        title = clip.get('generated_title', clip.get('outline', ''))
        content = clip.get('content', [])
        recommend_reason = clip.get('recommend_reason', '')
        
        # 计算视频时长
        start_time = clip.get('start_time', '00:00:00,000')
        end_time = clip.get('end_time', '00:00:00,000')
        duration = self._calculate_duration(start_time, end_time)
        
        # 分析内容特点
        content_text = ' '.join(content[:5]) if content else ''  # 取前5句作为分析基础
        
        # 生成更有价值的解说文稿
        if '节日' in title or '庆典' in title:
            opening = f"在这个特别的时刻，{title}正在上演。让我们一起走进这个充满魔力的世界。"
            main_content = f"这个片段展现了{title}的独特魅力。{recommend_reason}通过细腻的镜头语言和生动的对话，我们能够感受到其中蕴含的深层情感和文化内涵。"
            emotion_tone = "温馨"
        elif '冲突' in title or '战斗' in title:
            opening = f"紧张的时刻到了！{title}即将展开，让我们看看会发生什么。"
            main_content = f"这个片段展现了{title}的激烈场面。{recommend_reason}每一个细节都充满了张力和戏剧性，让人屏息凝神。"
            emotion_tone = "紧张"
        elif '情感' in title or '感动' in title:
            opening = f"这是一个关于{title}的动人故事，让我们一起感受其中的温暖。"
            main_content = f"这个片段展现了{title}的感人瞬间。{recommend_reason}通过细腻的情感表达，触动了我们内心最柔软的地方。"
            emotion_tone = "感动"
        else:
            opening = f"让我们深入探讨{title}这个话题，看看其中隐藏的精彩内容。"
            main_content = f"这个片段展现了{title}的精彩内容。{recommend_reason}通过专业的分析和深入的解读，我们能够发现其中蕴含的深层价值。"
            emotion_tone = "专业"
        
        closing = f"这就是{title}的精彩之处，它不仅展现了表面的内容，更蕴含着深刻的意义，值得我们反复品味和思考。"
        
        # 提取关键要点
        key_points = []
        if content:
            # 从内容中提取关键信息
            key_points.append(title)
            if len(content) > 2:
                key_points.append(content[2][:20] + "...")  # 第三句话的前20个字符
            key_points.append("深层价值")
        
        return {
            "opening": opening,
            "main_content": main_content,
            "closing": closing,
            "total_duration": duration,
            "key_points": key_points,
            "emotion_tone": emotion_tone,
            "target_audience": "内容爱好者"
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> int:
        """计算视频时长（秒）"""
        try:
            def time_to_seconds(time_str: str) -> float:
                parts = time_str.split(':')
                hours = int(parts[0])
                minutes = int(parts[1])
                seconds = float(parts[2].replace(',', '.'))
                return hours * 3600 + minutes * 60 + seconds
            
            start_seconds = time_to_seconds(start_time)
            end_seconds = time_to_seconds(end_time)
            return int(end_seconds - start_seconds)
        except:
            return 180  # 默认3分钟
    
    def save_clips_with_scripts(self, clips_with_scripts: List[Dict], output_path: Path):
        """保存带解说文稿的切片数据"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clips_with_scripts, f, ensure_ascii=False, indent=2)
        
        logger.info(f"带解说文稿的切片数据已保存到: {output_path}")

def run_step7_script(clips_with_titles_path: Path, output_path: Optional[Path] = None, metadata_dir: Optional[str] = None, prompt_files: Dict = None) -> List[Dict]:
    """
    运行第7步：解说文稿生成
    
    Args:
        clips_with_titles_path: 带标题的切片数据路径
        output_path: 输出路径，默认为step7_scripts.json
        metadata_dir: 元数据目录
        prompt_files: 提示词文件配置
        
    Returns:
        带解说文稿的切片数据列表
    """
    logger.info("🚀 开始第7步：解说文稿生成")
    
    # 读取带标题的切片数据
    with open(clips_with_titles_path, 'r', encoding='utf-8') as f:
        clips_with_titles = json.load(f)
    
    # 初始化生成器
    generator = ScriptGenerator(
        metadata_dir=Path(metadata_dir) if metadata_dir else None,
        prompt_files=prompt_files
    )
    
    # 生成解说文稿
    clips_with_scripts = generator.generate_scripts(clips_with_titles)
    
    # 保存结果
    if output_path is None:
        output_path = Path(metadata_dir) / "step7_scripts.json" if metadata_dir else METADATA_DIR / "step7_scripts.json"
    
    generator.save_clips_with_scripts(clips_with_scripts, output_path)
    
    logger.info(f"✅ 第7步完成，为 {len(clips_with_scripts)} 个片段生成了解说文稿")
    
    return clips_with_scripts 