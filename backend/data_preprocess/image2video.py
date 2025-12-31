"""
高速摄像图片转视频工具

功能：
1. 读取指定目录下所有文件夹中的图片
2. 按文件名顺序将图片合成为视频
3. 支持生成不同倍速的视频（放慢播放）
4. 支持并行处理多个文件夹
"""

import os
import re
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import cv2
import logging
import warnings

# 抑制 OpenCV 的警告信息（特别是中文路径相关的警告）
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
cv2.setLogLevel(0)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VideoConfig:
    """视频配置类"""
    def __init__(
        self,
        codec: str = 'mp4v',
        output_format: str = '.mp4',
        fps_list: List[float] = [30, 60, 90, 120, 160, 240]
    ):
        """
        初始化视频配置
        
        Args:
            codec: 视频编码器（默认mp4v）
            output_format: 输出视频格式（默认.mp4）
            fps_list: 要生成的视频帧率列表（默认[30, 60, 90, 120, 160, 240]）
                      原始采样频率4000Hz，用不同fps播放可以实现不同倍速的慢放效果
        """
        self.codec = codec
        self.output_format = output_format
        self.fps_list = fps_list


def get_image_files(folder_path: Path) -> List[Path]:
    """
    获取文件夹中所有图片文件，按文件名排序
    
    Args:
        folder_path: 文件夹路径
        
    Returns:
        排序后的图片文件路径列表
    """
    image_extensions = {'.jpeg', '.jpg', '.png', '.bmp'}
    image_files = []
    
    for file_path in folder_path.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            # 跳过比例尺图片
            if '比例尺' in file_path.name:
                continue
            image_files.append(file_path)
    
    # 按文件名自然排序
    def natural_sort_key(path: Path) -> List:
        """自然排序键函数，支持数字排序"""
        name = path.stem
        parts = re.split(r'(\d+)', name)
        return [int(part) if part.isdigit() else part.lower() for part in parts]
    
    image_files.sort(key=natural_sort_key)
    return image_files


def safe_read_image(image_path: Path) -> Optional[np.ndarray]:
    """
    安全地读取图片，处理中文路径和编码问题
    
    优先使用 numpy + imdecode 方式，避免 OpenCV 在 Windows 上处理中文路径的问题
    
    Args:
        image_path: 图片路径
        
    Returns:
        图片数组或None
    """
    try:
        # 方法1: 优先使用 numpy + imdecode，这样可以避免 OpenCV 的中文路径问题
        # 这是处理中文路径最可靠的方法
        with open(image_path, 'rb') as f:
            image_data = f.read()
            if len(image_data) == 0:
                return None
            
            # 使用 numpy 数组和 imdecode
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is not None and img.size > 0:
                return img
        
        # 方法2: 如果方法1失败，尝试直接使用 cv2.imread（可能会产生警告）
        # 注意：在 Windows 上，如果路径包含中文，这个方法可能会失败
        try:
            img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
            if img is not None and img.size > 0:
                return img
        except Exception:
            pass
            
    except FileNotFoundError:
        logger.debug(f"文件不存在: {image_path.name}")
    except PermissionError:
        logger.debug(f"没有权限读取文件: {image_path.name}")
    except Exception as e:
        logger.debug(f"读取图片失败 {image_path.name}: {type(e).__name__}: {e}")
    
    return None


def get_image_size(image_path: Path) -> Optional[tuple]:
    """
    获取图片尺寸
    
    Args:
        image_path: 图片路径
        
    Returns:
        (width, height) 或 None
    """
    img = safe_read_image(image_path)
    if img is not None:
        return (img.shape[1], img.shape[0])
    return None


def create_video_from_images(
    image_files: List[Path],
    output_path: Path,
    config: VideoConfig,
    fps: float = 30.0
) -> bool:
    """
    从图片列表创建视频
    
    Args:
        image_files: 图片文件路径列表
        output_path: 输出视频路径
        config: 视频配置
        fps: 视频帧率（原始采样频率4000Hz，用不同fps播放实现慢放效果）
        
    Returns:
        是否成功
    """
    if not image_files:
        logger.warning(f"没有图片文件，跳过: {output_path}")
        return False
    
    # 尝试获取图片尺寸，如果第一张失败，尝试其他图片
    width, height = None, None
    for img_path in image_files:
        image_size = get_image_size(img_path)
        if image_size is not None:
            width, height = image_size
            break
    
    if width is None or height is None:
        logger.error(f"无法从任何图片获取尺寸，跳过: {output_path}")
        return False
    
    # 确保输出目录存在
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建视频写入器
    # 注意：如果输出路径包含中文，VideoWriter 可能也有问题
    # 如果遇到问题，可以考虑使用临时文件然后重命名
    fourcc = cv2.VideoWriter_fourcc(*config.codec)
    
    # 尝试使用绝对路径的字符串形式
    output_path_str = str(output_path.resolve())
    out = cv2.VideoWriter(output_path_str, fourcc, fps, (width, height))
    
    if not out.isOpened():
        logger.error(f"无法创建视频文件: {output_path}")
        logger.error(f"  尝试的路径: {output_path_str}")
        return False
    
    try:
        successful_frames = 0
        failed_frames = 0
        
        for idx, image_path in enumerate(image_files):
            try:
                # 使用安全的图片读取方法
                img = safe_read_image(image_path)
                
                if img is None or img.size == 0:
                    failed_frames += 1
                    if failed_frames <= 5:  # 只记录前5个失败的文件
                        logger.warning(f"无法读取图片，跳过: {image_path.name}")
                    continue
                
                # 如果图片尺寸不一致，调整大小
                if img.shape[1] != width or img.shape[0] != height:
                    img = cv2.resize(img, (width, height))
                
                out.write(img)
                successful_frames += 1
                    
            except Exception as e:
                failed_frames += 1
                if failed_frames <= 5:
                    logger.warning(f"处理图片时出错 {image_path.name}: {e}")
                continue
        
        if successful_frames == 0:
            logger.error(f"没有成功处理任何图片，视频创建失败: {output_path}")
            return False
        
        if failed_frames > 0:
            logger.warning(f"视频创建完成但有 {failed_frames} 张图片处理失败: {output_path.name}")
        
        return True
        
    except Exception as e:
        logger.error(f"创建视频时出错 {output_path}: {e}")
        return False
    finally:
        out.release()


def process_folder(
    folder_path: Path,
    output_base_path: Path,
    config: VideoConfig
) -> Dict[str, bool]:
    """
    处理单个文件夹，生成多个倍速的视频
    
    Args:
        folder_path: 输入文件夹路径
        output_base_path: 输出基础路径
        config: 视频配置
        
    Returns:
        处理结果字典 {视频文件名: 是否成功}
    """
    folder_name = folder_path.name
    logger.info(f"开始处理文件夹: {folder_name}")
    
    # 获取所有图片文件
    image_files = get_image_files(folder_path)
    
    if not image_files:
        logger.warning(f"文件夹中没有图片: {folder_name}")
        return {}
    
    logger.info(f"找到 {len(image_files)} 张图片: {folder_name}")
    
    results = {}
    
    # 创建以原文件夹名命名的子文件夹
    output_folder = output_base_path / folder_name
    output_folder.mkdir(parents=True, exist_ok=True)
    
    # 为每个fps生成视频
    for fps in config.fps_list:
        # 生成输出文件名，使用fps作为后缀
        video_name = f"{folder_name}_fps{int(fps)}{config.output_format}"
        
        output_path = output_folder / video_name
        
        # 创建视频
        success = create_video_from_images(
            image_files,
            output_path,
            config,
            fps
        )
        
        results[video_name] = success
    
    # 文件夹处理完成，输出结果
    successful_videos = sum(1 for s in results.values() if s)
    total_videos = len(results)
    if successful_videos == total_videos:
        logger.info(f"✓ 文件夹处理完成: {folder_name} (成功: {successful_videos}/{total_videos})")
    else:
        logger.warning(f"⚠ 文件夹处理完成: {folder_name} (成功: {successful_videos}/{total_videos})")
    
    return results


def process_all_folders(
    input_path: str,
    output_path: str,
    config: Optional[VideoConfig] = None,
    max_workers: int = 16
) -> Dict[str, Dict[str, bool]]:
    """
    并行处理所有文件夹
    
    Args:
        input_path: 输入目录路径（包含多个文件夹的目录）
        output_path: 输出目录路径
        config: 视频配置，如果为None则使用默认配置
        max_workers: 最大并行工作线程数
        
    Returns:
        处理结果字典 {文件夹名: {视频文件名: 是否成功}}
    """
    input_dir = Path(input_path)
    output_dir = Path(output_path)
    
    # 创建输出目录
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if not input_dir.exists():
        logger.error(f"输入目录不存在: {input_path}")
        return {}
    
    if config is None:
        config = VideoConfig()
    
    # 获取所有子文件夹
    folders = [f for f in input_dir.iterdir() if f.is_dir()]
    
    if not folders:
        logger.warning(f"输入目录中没有子文件夹: {input_path}")
        return {}
    
    logger.info(f"找到 {len(folders)} 个文件夹，开始并行处理...")
    
    all_results = {}
    
    # 使用线程池并行处理
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_folder = {
            executor.submit(process_folder, folder, output_dir, config): folder
            for folder in folders
        }
        
        # 收集结果
        for future in as_completed(future_to_folder):
            folder = future_to_folder[future]
            try:
                results = future.result()
                all_results[folder.name] = results
            except Exception as e:
                logger.error(f"处理文件夹时出错 {folder.name}: {e}")
                all_results[folder.name] = {}
    
    # 输出统计信息
    total_folders = len(all_results)
    successful_folders = sum(1 for r in all_results.values() if any(r.values()))
    total_videos = sum(len(r) for r in all_results.values())
    successful_videos = sum(sum(1 for s in r.values() if s) for r in all_results.values())
    
    logger.info("=" * 60)
    logger.info("处理完成统计:")
    logger.info(f"  总文件夹数: {total_folders}")
    logger.info(f"  成功处理文件夹数: {successful_folders}")
    logger.info(f"  总视频数: {total_videos}")
    logger.info(f"  成功生成视频数: {successful_videos}")
    logger.info("=" * 60)
    
    return all_results


def main():
    """主函数"""
    # 配置路径
    input_path = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据\高速摄像"
    output_path = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据\高速摄像合成video"
    
    # 配置视频参数
    # 原始采样频率4000Hz，用不同fps播放可以实现不同倍速的慢放效果
    # 例如：30fps播放 = 4000/30 = 133.33倍慢速，240fps播放 = 4000/240 = 16.67倍慢速
    config = VideoConfig(
        codec='mp4v',  # 视频编码器
        output_format='.mp4',
        fps_list=[30, 60, 90, 120, 160, 240]  # 生成不同fps的视频
    )
    
    # 并行处理所有文件夹
    results = process_all_folders(
        input_path=input_path,
        output_path=output_path,
        config=config,
        max_workers=32  # 可以根据CPU核心数调整
    )
    
    return results


if __name__ == "__main__":
    main()

