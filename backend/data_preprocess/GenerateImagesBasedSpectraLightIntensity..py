import os
import glob
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys
from pathlib import Path

# 添加backend目录到Python路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# 导入logger
from utils.logger import get_logger

# 初始化logger
logger = get_logger(__name__)

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei'] 
plt.rcParams['axes.unicode_minus'] = False

# ==========================================
# 工具函数：目录创建
# ==========================================
def create_sub_dirs(base_path, sub_folders):
    """在源文件夹下创建多个子文件夹"""
    paths = {}
    image_root = os.path.join(base_path, "image")
    if not os.path.exists(image_root):
        os.makedirs(image_root)
    
    for sub in sub_folders:
        path = os.path.join(image_root, sub)
        if not os.path.exists(path):
            os.makedirs(path)
        paths[sub] = path
    return paths

def get_longest_segment(bool_array):
    """
    返回最长连续 True 片段的 [start, end) 索引
    """
    mask = np.asarray(bool_array, dtype=bool).astype(np.int8)  # 关键：转成 0/1
    d = np.diff(np.concatenate(([0], mask, [0])))             # diff 后才会有 +1/-1

    start_indices = np.where(d == 1)[0]
    end_indices   = np.where(d == -1)[0]

    if start_indices.size == 0:
        return None, None

    lengths = end_indices - start_indices
    max_idx = np.argmax(lengths)
    return int(start_indices[max_idx]), int(end_indices[max_idx])


# # ==========================================
# # 核心算法：判断焊接起止时刻 (抗干扰版)
# # ==========================================
def detect_welding_interval(data_array, fs, threshold_ratio=0.15, use_adaptive=True):
    """
    【双阈值扩散版】判断焊接的开始、结束及持续时间
    解决“漏检”问题：先锁定高可信的核心区域，然后向左右延伸直到信号消失。
    
    Args:
        data_array: 信号数据
        fs: 采样频率
        threshold_ratio: 核心区域判定阈值 (默认 0.15)
        use_adaptive: (保留参数，本函数使用更稳健的双阈值逻辑)
    
    Returns:
        (start_index, end_index, start_time, end_time, duration)
    """
    # 0. 基础清洗与检查
    data_array = np.array(data_array).flatten()
    data_array = np.nan_to_num(data_array)
    n = len(data_array)
    if n < 5: 
        return 0, 0, 0.0, 0.0, 0.0

    # 1. 计算基线噪音 (Baseline Noise)
    # 取数据最小的 10% 的平均值作为基线底噪，比直接取 min 更抗干扰
    sorted_data = np.sort(data_array)
    baseline = np.mean(sorted_data[:int(n * 0.1)]) 
    norm_data = data_array - baseline
    
    # 极值检查
    max_val = np.max(norm_data)
    if max_val < 1e-6:
        return 0, 0, 0.0, 0.0, 0.0

    # 2. 信号平滑 (Smoothing)
    # 必须平滑，否则向外搜索时容易被一个噪点截断
    window_size = int(fs * 0.005) # 5ms 窗口
    if window_size < 3: window_size = 3
    smooth_series = pd.Series(norm_data).rolling(window=window_size, center=True, min_periods=1).mean()
    smooth_data = smooth_series.values

    # =======================================================
    # 核心逻辑：双阈值法 (Double Thresholding / Hysteresis-like)
    # =======================================================
    
    # 3. 定义两个阈值
    # 高阈值：用于确定“这里肯定是焊接中” (Core)
    high_threshold = max_val * threshold_ratio 
    # 低阈值：用于确定“哪里才算彻底没信号” (Edge) -> 解决结束早、开始晚的问题
    # 设置为最大值的 2% 或者 一个极小的固定值，视情况而定
    low_threshold = max_val * 0.02 

    # 4. 第一步：找到核心区域 (Core Region)
    # 只要超过高阈值，就认为是核心区
    is_core = smooth_data > high_threshold
    
    # 提取最长的核心区域 (避免闪烁干扰)
    core_start, core_end = get_longest_segment(is_core)
    
    if core_start is None:
        return 0, 0, 0.0, 0.0, 0.0
        
    # 5. 第二步：向外扩散搜索 (Expansion)
    # 从 core_start 向左走，直到低于 low_threshold
    # 从 core_end 向右走，直到低于 low_threshold
    
    # 向左搜索 (找开始点)
    final_start = core_start
    # while 循环：只要没到头 且 信号依然大于低阈值，就继续往左移
    while final_start > 0 and smooth_data[final_start - 1] > low_threshold:
        final_start -= 1
        
    # 向右搜索 (找结束点)
    final_end = core_end
    # while 循环：只要没到头 且 信号依然大于低阈值，就继续往右移
    while final_end < n - 1 and smooth_data[final_end + 1] > low_threshold:
        final_end += 1
    
    # 6. 计算结果
    start_time = final_start / fs
    end_time = final_end / fs
    duration = end_time - start_time
    
    return int(final_start), int(final_end), float(start_time), float(end_time), float(duration)


def detect_welding_interval_photodiode(df, fs, threshold_ratio=0.15):
    """
    专门用于光强信号的焊接区间检测
    只使用【红外光 (Infrared)】进行判断。
    红外光在开始和结束时为0，中间突变，因此使用自适应突变检测非常精确。
    
    Args:
        df: 包含Visible, Reflected, Infrared列的DataFrame
        fs: 采样频率
        threshold_ratio: 阈值比例
        
    Returns:
        (start_index, end_index, start_time, end_time, duration)
    """
    # 提取红外光信号
    ir_signal = df['Infrared'].values
    
    # 传入新的抗干扰检测函数
    return detect_welding_interval(ir_signal, fs, threshold_ratio=threshold_ratio)

# ==========================================
# 绘图核心逻辑
# ==========================================
def plot_channel(ax, time_axis, data, label, color, plot_mode='line'):
    """绘制单个通道的数据，支持折线和散点"""
    if plot_mode == 'scatter':
        # 散点模式：s=2 表示点的大小，alpha=0.6 透明度
        ax.scatter(time_axis, data, label=label, color=color, s=2, alpha=0.6, edgecolors='none')
    else:
        # 折线模式：linewidth=0.3 极细的线，防止密集时糊成一团
        ax.plot(time_axis, data, label=label, color=color, alpha=0.8, linewidth=0.3)

# ==========================================
# 辅助绘图：绘制起止时间线
# # ==========================================
def add_time_markers(ax, start_t, end_t, color='black', is_horizontal=False):
    """
    在图上绘制开始和结束的时间线（仅显示两端 25% 的长度，且线条更细）
    """
    # 获取当前坐标轴的范围
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    
    # 设置线条宽度（更细）
    lw = 0.8 
    # 计算 25% 的跨度
    x_span = x_max - x_min
    y_span = y_max - y_min
    
    if is_horizontal:
        # --- 水平线逻辑 (用于热力图) ---
        # 绘制左侧 25% 和右侧 25%
        for t in [start_t, end_t]:
            # 左段
            ax.plot([x_min, x_min + x_span * 0.25], [t, t], color=color, linestyle='--', linewidth=lw, alpha=0.9)
            # 右段
            ax.plot([x_max - x_span * 0.25, x_max], [t, t], color=color, linestyle='--', linewidth=lw, alpha=0.9)
            
            label_text = 'Start' if t == start_t else 'End'
            ax.text(x_min, t, f' {label_text}: {t:.3f}s', 
                    color=color, fontsize=8, va='bottom', weight='bold')
    else:
        # --- 垂直线逻辑 (用于折线图/散点图) ---
        # 计算文字高度位置
        text_y_pos = y_max - y_span * 0.05
        
        for t in [start_t, end_t]:
            # 下段 (前 25%)
            ax.plot([t, t], [y_min, y_min + y_span * 0.25], color=color, linestyle='--', linewidth=lw, alpha=0.8)
            # 上段 (后 25%)
            ax.plot([t, t], [y_max - y_span * 0.25, y_max], color=color, linestyle='--', linewidth=lw, alpha=0.8)
            
            label_text = 'Start' if t == start_t else 'End'
            ax.text(t, text_y_pos, f' {label_text}\n {t:.3f}s', 
                    color=color, fontsize=8, ha='left', va='top', weight='bold')
        # 垂直线（用于折线图/散点图）
        y_min, y_max = ax.get_ylim()
        text_y_pos = y_max - (y_max - y_min) * 0.05
        ax.axvline(x=start_t, color=color, linestyle='--', linewidth=1.5, alpha=0.8, label='Start/End')
        ax.text(start_t, text_y_pos, f' Start\n {start_t:.3f}s', color=color, fontsize=9, ha='left', va='top', weight='bold')
        ax.axvline(x=end_t, color=color, linestyle='--', linewidth=1.5, alpha=0.8)
        ax.text(end_t, text_y_pos, f' End\n {end_t:.3f}s', color=color, fontsize=9, ha='left', va='top', weight='bold')


# ==========================================
# 绘图函数：光强信号绘图
# ==========================================
def plot_photodiode_data(
    df, time_axis, start_t, end_t, duration, total_seconds,
    original_name, dir_map, plot_mode='line'
):
    """
    绘制光强信号的图表
    
    Args:
        df: 包含Visible, Reflected, Infrared列的DataFrame
        time_axis: 时间轴数组
        start_t: 焊接开始时间
        end_t: 焊接结束时间
        duration: 焊接持续时间
        total_seconds: 总时长
        original_name: 原始文件名
        dir_map: 保存目录映射字典
        plot_mode: 'line' 或 'scatter'
    """
    title_str = f"{original_name}\nTotal: {total_seconds:.4f}s | Active: {start_t:.4f}s - {end_t:.4f}s | Dur: {duration:.4f}s"
    
    # 定义要画的4张图的配置
    tasks = [
        (['Visible'], 'Visible', ['blue'], "可见光强度"),
        (['Reflected'], 'Reflected', ['green'], "反射光强度"),
        (['Infrared'], 'Infrared', ['red'], "红外光强度"),
        (['Visible', 'Reflected', 'Infrared'], 'Combined', ['blue', 'green', 'red'], "光强信号合并")
    ]
    
    for cols, folder_key, colors, ylabel in tasks:
        # 设置画布大小
        figsize = (20, 6) if plot_mode == 'line' else (14, 6)
        fig, ax = plt.subplots(figsize=figsize, dpi=100) # 屏幕显示dpi
        
        # 循环绘制当前图所需的通道
        max_y_in_plot = 0
        for col_name, color in zip(cols, colors):
            plot_channel(ax, time_axis, df[col_name], col_name, color, plot_mode)
            current_max = df[col_name].max()
            if not np.isnan(current_max):
                max_y_in_plot = max(max_y_in_plot, current_max)
        
        # 设置标题和标签
        ax.set_title(f"光强信号 - {ylabel} - {title_str}", fontsize=10)
        ax.set_xlabel("时间 (Time) [s]")
        ax.set_ylabel("强度/电压 (V)")
        
        # Y轴自动缩放优化
        if max_y_in_plot > 0:
            ax.set_ylim(-0.001, max_y_in_plot * 1.1)
        
        # 绘制起止时间线
        if duration > 0:
            add_time_markers(ax, start_t, end_t, color='black')

        ax.legend(loc='upper right')
        ax.grid(True, linestyle='--', alpha=0.4)
        
        # 【修改】保存为 PNG 且 dpi=300
        save_name = os.path.splitext(original_name)[0] + ".png"
        plt.savefig(os.path.join(dir_map[folder_key], save_name), format='png', dpi=300, bbox_inches='tight')
        plt.close(fig)


# ==========================================
# 绘图函数：光谱信号绘图
# ==========================================
def plot_spectrometer_data(
    intensity_matrix, wavelengths, start_t, end_t, duration, total_seconds,
    original_name, dir_map
):
    """
    绘制光谱信号的热力图
    
    Args:
        intensity_matrix: 强度矩阵 (行=时间, 列=波长)
        wavelengths: 波长列表
        start_t: 焊接开始时间
        end_t: 焊接结束时间
        duration: 焊接持续时间
        total_seconds: 总时长
        original_name: 原始文件名
        dir_map: 保存目录映射字典
    """
    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)
    title_str = f"{original_name}\nTotal: {total_seconds:.4f}s | Active: {start_t:.4f}s - {end_t:.4f}s | Dur: {duration:.4f}s"
    
    if len(wavelengths) > 0 and len(intensity_matrix) > 0:
        im = ax.imshow(intensity_matrix, aspect='auto', cmap='jet', 
                   extent=[min(wavelengths), max(wavelengths), total_seconds, 0])
        
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('光谱强度')
        
        ax.set_title(f"光谱时域演变图 - {title_str}")
        ax.set_xlabel("波长 (nm)")
        ax.set_ylabel("时间 (s)")

        # 绘制起止时间线（水平线）
        if duration > 0:
            add_time_markers(ax, start_t, end_t, color='white', is_horizontal=True)

        # 【修改】保存为 PNG 且 dpi=300
        save_name = os.path.splitext(original_name)[0] + ".png"
        plt.savefig(os.path.join(dir_map["Spectrogram"], save_name), format='png', dpi=300, bbox_inches='tight')
        print(f"光谱图保存: {save_name}")
    
    plt.close(fig)

# ==========================================
# 获取标准化的文件名 Key
# ==========================================
def get_standard_key(filename):
    """
    清洗文件名，确保匹配成功率。
    1. 去除首尾空格 (.strip())
    2. 强制转为小写 (.lower()) -> 解决大小写不匹配问题
    """
    clean_name = filename.strip().lower()
    return clean_name

# ==========================================
# 1. 光强信号处理函数
# ==========================================
def process_photodiode_data(folder_path, master_data, plot_mode='line'):
    """
    处理光强信号并更新 master_data
    :param plot_mode: 'line' (折线图，X轴拉长) 或 'scatter' (散点图)
    """
    logger.info("-" * 50)
    logger.info(f"开始处理光强信号: {folder_path} [模式: {plot_mode}]")
    
    # 检查路径是否存在
    if not os.path.exists(folder_path):
        logger.error(f"光强信号路径不存在: {folder_path}")
        return
    
    files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not files:
        logger.warning(f"未找到txt文件: {folder_path}")
        return
    
    logger.info(f"找到 {len(files)} 个txt文件")

    # 创建分类文件夹
    dir_map = create_sub_dirs(folder_path, ["Visible", "Reflected", "Infrared", "Combined"])

    for file_path in files:
        original_name = os.path.basename(file_path)
        # 【修改点】获取标准化 Key (小写)
        match_key = get_standard_key(original_name)
        
        logger.info(f"处理光强: {original_name}")
        
        # 初始化 master_data
        if match_key not in master_data:
            master_data[match_key] = {"photodiode": None, "spectrometer": None, "comparison": None}

        try:
            # 1. 读取采样频率
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                first_line = f.readline()
                try:
                    fs = float(first_line.split('\t')[-1])
                    logger.info(f"采样频率: {fs}")
                except:
                    fs = 20000 
                    logger.warning(f"采样频率读取失败，使用默认值20000: {original_name}")
            
            # 2. 读取数据 (GBK编码)
            df = pd.read_csv(file_path, skiprows=1, sep='\t', header=None, encoding='gbk')
            df = df.dropna(axis=1, how='all')
            
            if df.shape[1] >= 3:
                df = df.iloc[:, :3]
                df.columns = ['Visible', 'Reflected', 'Infrared']
            else:
                logger.warning(f"列数不足，跳过: {original_name}")
                continue
            
            # 3. 生成时间轴
            total_rows = len(df)
            total_seconds = total_rows / fs
            time_axis = np.arange(total_rows) / fs
            
            # 4. 算法：判断焊接起止
            # 【注意】这里现在只用红外光判定
            start_idx, end_idx, start_t, end_t, duration = detect_welding_interval_photodiode(df, fs, threshold_ratio=0.15)
            
            # 5. 更新 master_data
            master_data[match_key]["photodiode"] = {
                "original_filename": original_name, # 保留原始文件名用于显示
                "fs": fs,
                "total_rows": total_rows,
                "total_file_seconds": round(total_seconds, 6),
                "welding_start_sec": round(start_t, 6),
                "welding_end_sec": round(end_t, 6),
                "welding_duration_sec": round(duration, 6),
                "welding_start_idx": start_idx,
                "welding_end_idx": end_idx
            }
            
            # 6. 绘图 (生成 PNG)
            plot_photodiode_data(
                df, time_axis, start_t, end_t, duration, total_seconds,
                original_name, dir_map, plot_mode
            )
            logger.info(f"光强文件处理完成: {original_name}")
                
        except Exception as e:
            logger.error(f"处理光强文件 {original_name} 出错: {e}", exc_info=True)

# ==========================================
# 2. 光谱信号处理函数
# ==========================================
def process_spectrometer_data(folder_path, master_data):
    """
    处理光谱信号并更新 master_data
    """
    logger.info("-" * 50)
    logger.info(f"开始处理光谱信号: {folder_path}")
    
    # 检查路径是否存在
    if not os.path.exists(folder_path):
        logger.error(f"光谱信号路径不存在: {folder_path}")
        return
    
    files = glob.glob(os.path.join(folder_path, "*.txt"))
    if not files:
        logger.warning(f"未找到txt文件: {folder_path}")
        return
    
    logger.info(f"找到 {len(files)} 个txt文件")

    dir_map = create_sub_dirs(folder_path, ["Spectrogram"])

    for file_path in files:
        original_name = os.path.basename(file_path)
        # 【修改点】获取标准化 Key (小写)
        match_key = get_standard_key(original_name)
        
        logger.info(f"处理光谱: {original_name}")
        
        if match_key not in master_data:
            master_data[match_key] = {"photodiode": None, "spectrometer": None, "comparison": None}
        
        try:
            # 读取数据
            df = pd.read_csv(file_path, skiprows=1, sep='\t', encoding='gbk')
            df = df.dropna(axis=1, how='all')
            
            # 提取有效波长列
            wavelengths = []
            valid_cols = []
            for col in df.columns:
                try:
                    wl = float(col)
                    wavelengths.append(wl)
                    valid_cols.append(col)
                except:
                    pass
            
            # 数据矩阵 (行=时间, 列=波长)
            intensity_matrix = df[valid_cols].values
            
            # 估算频率 (假设200Hz, 5ms)
            # 注意：如果文件头有具体频率，最好解析文件头，这里沿用之前的假设
            fs_spec = 200.0 
            total_rows = len(intensity_matrix)
            total_seconds = total_rows / fs_spec
            
            # 算法：判断光谱焊接起止
            # 计算每一行的总光强
            total_intensity_per_row = np.sum(intensity_matrix, axis=1)
            start_idx, end_idx, start_t, end_t, duration = detect_welding_interval(total_intensity_per_row, fs_spec)
            logger.info(f"光谱检测结果 - start_idx: {start_idx}, end_idx: {end_idx}, start_t: {start_t:.4f}s, end_t: {end_t:.4f}s, duration: {duration:.4f}s")
            master_data[match_key]["spectrometer"] = {
                "original_filename": original_name,
                "fs": fs_spec,
                "total_rows": total_rows,
                "total_file_seconds": round(total_seconds, 6),
                "welding_start_sec": round(start_t, 6),
                "welding_end_sec": round(end_t, 6),
                "welding_duration_sec": round(duration, 6),
                "welding_start_idx": start_idx,
                "welding_end_idx": end_idx
            }
            
            # 绘图 (热力图) - 使用抽离的绘图函数
            plot_spectrometer_data(
                intensity_matrix, wavelengths, start_t, end_t, duration, total_seconds,
                original_name, dir_map
            )
            logger.info(f"光谱文件处理完成: {original_name}")
            
        except Exception as e:
            logger.error(f"处理光谱文件 {original_name} 出错: {e}", exc_info=True)

# ==========================================
# 3. 对比计算函数
# ==========================================
def calculate_comparison_metrics(master_data):
    """
    遍历 master_data，计算光强与光谱的误差
    """
    logger.info("-" * 50)
    logger.info("开始计算误差对照...")
    
    for file_name, data in master_data.items():
        pd_data = data.get("photodiode")
        sp_data = data.get("spectrometer")
        
        # 如果任一数据缺失，则无法对比，留空
        if pd_data is None or sp_data is None:
            data["comparison"] = None
            continue
        
        # 获取持续时间
        dur_pd = pd_data["welding_duration_sec"]
        dur_sp = sp_data["welding_duration_sec"]
        
        # 计算差值 (绝对值)
        diff_abs = abs(dur_pd - dur_sp)
        
        # 计算误差比率
        # 根据需求：差值 / 整体秒数 (Total File Seconds)
        # 这里优先使用光谱的总时长作为分母，因为光谱记录时间通常更长，是更完整的观测窗口
        # 如果光谱总时长异常为0，则用光强的
        total_time_ref = sp_data["total_file_seconds"]
        if total_time_ref == 0:
            total_time_ref = pd_data["total_file_seconds"]
            
        error_ratio = diff_abs / total_time_ref if total_time_ref > 0 else 0.0
        
        data["comparison"] = {
            "duration_diff_sec": round(diff_abs, 6),
            "reference_total_seconds": total_time_ref,
            "error_ratio": round(error_ratio, 8),
            "note": "Reference total seconds based on Spectrometer file length by default"
        }

# ==========================================
# 主程序入口
# ==========================================
if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("开始执行焊接数据分析程序")
    logger.info("=" * 60)
    
    # 定义路径 - 使用存在的路径
    path_photodiode = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据\光强信号_第一列 可见光_第二列 反射光_第三列_红外光"
    path_spectrometer = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据\光谱信号"
    # path_photodiode = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据_三者均有\光强信号_第一列 可见光_第二列 反射光_第三列_红外光"
    # path_spectrometer = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据_三者均有\光谱信号"
    
    # 主数据字典：Key = 文件名
    master_data = {}
    
    # 1. 处理光强信号
    # 参数 plot_mode 可以选 'line' (折线, 拉长) 或 'scatter' (散点)
    # 建议先用 'line' 看看，如果不喜欢竖线，改成 'scatter'
    if os.path.exists(path_photodiode):
        logger.info(f"开始处理光强信号: {path_photodiode}")
        process_photodiode_data(path_photodiode, master_data, plot_mode='scatter')
    else:
        logger.error(f"光强信号路径不存在: {path_photodiode}")
    
    # 2. 处理光谱信号
    if os.path.exists(path_spectrometer):
        logger.info(f"开始处理光谱信号: {path_spectrometer}")
        process_spectrometer_data(path_spectrometer, master_data)
    else:
        logger.error(f"光谱信号路径不存在: {path_spectrometer}")

    # 3. 计算误差对照
    calculate_comparison_metrics(master_data)
    
    # 4. 保存 JSON
    # 保存在光强文件夹的上级目录
    json_save_path = os.path.join(os.path.dirname(path_photodiode), "welding_analysis_report.json")
    
    try:
        with open(json_save_path, 'w', encoding='utf-8') as f:
            json.dump(master_data, f, indent=4, ensure_ascii=False)
        logger.info(f"分析报告已生成: {json_save_path}")
        logger.info("Json包含: 光强分析、光谱分析、以及两者持续时间的误差对比。")
    except Exception as e:
        logger.error(f"保存JSON失败: {e}", exc_info=True)
    
    logger.info("=" * 60)
    logger.info("程序执行完成")
    logger.info("=" * 60)