import os
import json
import re
import sys
from pathlib import Path

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger

# 初始化日志记录器
logger = get_logger(__name__)

# ================= 配置区域 =================
def get_base_path():
    """获取数据根目录的相对路径"""
    # 脚本所在目录: backend/scripts
    script_dir = Path(__file__).parent
    # 向上两级到项目根目录，再进入 data 目录
    base_path = script_dir.parent.parent / "data" / "3mm复合材料和铝合金焊接数据" / "3mm复合材料和铝合金焊接数据"
    return str(base_path)

# 定义各子文件夹名称
DIR_HS_CAM = "高速摄像"
DIR_VIDEO = "高速摄像合成video"
DIR_SPEC = os.path.join("光谱信号", "image", "Spectrogram") # 注意这里中间有 image 层
DIR_PD = os.path.join("光强信号_第一列 可见光_第二列 反射光_第三列_红外光", "image", "Combined")

# 允许的图片扩展名
VALID_EXTS = ('.jpg', '.jpeg', '.png', '.bmp')
# 允许的视频扩展名
VIDEO_EXTS = ('.mp4', '.avi', '.mov')

# ================= 工具函数 =================
def find_file_insensitive(target_name, search_dir):
    """
    在 search_dir 中查找文件名包含 target_name 的文件 (不区分大小写)
    返回: 相对路径 (相对于 search_dir) 或 None
    """
    if not os.path.exists(search_dir):
        return None
    
    # 获取目录下所有文件
    try:
        files = os.listdir(search_dir)
    except Exception as e:
        logger.error(f"❌ 无法读取目录: {search_dir}, 错误: {e}")
        return None

    target_lower = target_name.lower()
    
    # 1. 尝试精确匹配 (文件名包含实验ID)
    for f in files:
        if f.lower().startswith(target_lower) and f.lower().endswith(VALID_EXTS):
            return f  # 返回真实的文件名
    
    # 2. 如果没找到，尝试宽松匹配 (实验ID包含文件名，或文件名包含实验ID)
    # 这一步是为了防止文件名多了一些后缀
    for f in files:
        f_name_no_ext = os.path.splitext(f)[0]
        if (target_lower in f.lower() or f_name_no_ext.lower() in target_lower) and f.lower().endswith(VALID_EXTS):
            return f

    return None

def get_hs_image_info(exp_dir):
    """获取高速摄像文件夹下的图片信息"""
    try:
        files = [f for f in os.listdir(exp_dir) if f.lower().endswith(VALID_EXTS)]
    except:
        return 0, 0, 0, ""

    if not files:
        return 0, 0, 0, ""

    # 解析数字
    nums = []
    digits = 0
    ext = ".jpg" # 默认
    
    # 抽样检查第一个文件的后缀
    if files:
        ext = os.path.splitext(files[0])[1]

    for f in files:
        # 提取 File_xxxxx 中的数字
        match = re.search(r'File_(\d+)', f, re.IGNORECASE)
        if match:
            n_str = match.group(1)
            nums.append(int(n_str))
            digits = len(n_str) # 记录位数
    
    if not nums:
        return 0, 0, 0, ""
    
    nums.sort()
    return nums[0], len(nums), digits, ext

def find_videos_in_folder(exp_name, base_path):
    """
    在视频文件夹中查找指定实验的所有视频文件
    返回: 视频列表 [{"fps": 30, "path": "相对路径"}, ...]
    """
    video_folder = os.path.join(base_path, DIR_VIDEO, exp_name)
    
    if not os.path.exists(video_folder):
        return []
    
    videos = []
    try:
        files = os.listdir(video_folder)
        for f in files:
            if f.lower().endswith(VIDEO_EXTS):
                # 尝试从文件名中提取 fps，例如: A1_SiC_800W_26_fps30.mp4
                match = re.search(r'_fps(\d+)', f, re.IGNORECASE)
                fps = int(match.group(1)) if match else 0
                
                # 构建相对路径（供前端使用）
                rel_path = f"{DIR_VIDEO}/{exp_name}/{f}".replace("\\", "/")
                videos.append({
                    "fps": fps,
                    "path": rel_path,
                    "filename": f
                })
    except Exception as e:
        logger.warning(f"   ⚠️ 读取视频文件夹出错: {e}")
        return []
    
    # 按 fps 排序
    videos.sort(key=lambda x: x["fps"])
    return videos

# ================= 主逻辑 =================
def scan_welding_data():
    """扫描焊接数据并生成数据库文件"""
    base_path = get_base_path()
    output_data = []
    hs_root = os.path.join(base_path, DIR_HS_CAM)

    logger.info(f"🔍 开始扫描根目录: {hs_root}")

    if not os.path.exists(hs_root):
        logger.error(f"❌ 严重错误: 找不到高速摄像目录 -> {hs_root}")
        logger.error(f"当前脚本位置: {Path(__file__).parent}")
        logger.error("请检查相对路径设置是否正确！")
        return output_data
    
    # 获取所有实验文件夹
    exp_folders = [f for f in os.listdir(hs_root) if os.path.isdir(os.path.join(hs_root, f))]
    logger.info(f"📂 发现 {len(exp_folders)} 个实验文件夹")

    for exp_name in exp_folders:
        logger.info(f"--- 处理实验: {exp_name} ---")
        exp_path = os.path.join(hs_root, exp_name)
        
        # 1. 获取高速图片信息
        start_idx, total, digits, hs_ext = get_hs_image_info(exp_path)
        if total == 0:
            logger.warning(f"   ⚠️ 跳过: 文件夹为空或无图片")
            continue
        
        # 2. 查找光谱图
        spec_full_dir = os.path.join(base_path, DIR_SPEC)
        spec_file = find_file_insensitive(exp_name, spec_full_dir)
        spec_web_path = f"{DIR_SPEC}/{spec_file}".replace("\\", "/") if spec_file else ""
        if not spec_file:
            logger.warning(f"   ⚠️ 未找到光谱图 (在 {DIR_SPEC} 中搜 {exp_name})")

        # 3. 查找光强图
        pd_full_dir = os.path.join(base_path, DIR_PD)
        pd_file = find_file_insensitive(exp_name, pd_full_dir)
        pd_web_path = f"{DIR_PD}/{pd_file}".replace("\\", "/") if pd_file else ""
        if not pd_file:
            logger.warning(f"   ⚠️ 未找到光强图(在 {DIR_PD} 中搜 {exp_name})")
        
        # 4. 查找视频文件
        videos = find_videos_in_folder(exp_name, base_path)
        has_video = len(videos) > 0
        
        if has_video:
            logger.info(f"   ✅ 找到 {len(videos)} 个视频: {[v['filename'] for v in videos]}")
        else:
            logger.warning(f"   ⚠️ 未找到视频文件")

        # 解析参数用于显示
        parts = exp_name.split('_')
        mat = parts[1] if len(parts) > 1 else "Unknown"
        power = parts[2] if len(parts) > 2 else "-"
        speed = parts[3] if len(parts) > 3 else "-"

        exp_data = {
            "id": exp_name,
            "mat": mat, 
            "power": power, 
            "speed": speed,
            "start_idx": start_idx,
            "total": total,
            "digits": digits,
            "hs_ext": hs_ext,
            "spec_path": spec_web_path,
            "pd_path": pd_web_path,
            "has_video": has_video,
            "videos": videos  # 添加视频列表
        }
        output_data.append(exp_data)
        logger.info(f"   ✅ 成功: {total} 帧, 起始 {start_idx}, 光谱={'有' if spec_file else '无'}, 视频={'有' if has_video else '无'}")

    return output_data

def generate_js_file(output_data, output_file=None):
    """生成 JavaScript 数据文件"""
    if output_file is None:
        # 计算相对于 backend/scripts 的前端 public 路径
        script_dir = Path(__file__).parent
        output_file = script_dir.parent.parent / "frontend" / "public" / "welding_data.js"
    
    js_content = f"const WELDING_DB = {json.dumps(output_data, indent=2, ensure_ascii=False)};"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(js_content)
    
    logger.info(f"🎉 扫描完成! 生成了 {len(output_data)} 条数据到 {output_file}")

def main():
    """主函数入口"""
    output_data = scan_welding_data()
    if output_data:
        generate_js_file(output_data)
    else:
        logger.error("❌ 未扫描到任何数据，请检查路径配置")

if __name__ == "__main__":
    main()