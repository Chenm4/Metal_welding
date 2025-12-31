"""
比对三个数据文件夹中的文件名

功能：
1. 读取三个文件夹中的所有文件名
2. 去除后缀后比对，找出共同的和独有的文件
3. 生成可视化图表展示文件分布情况
"""

import os
import re
import shutil
from pathlib import Path
from typing import Set, Dict, List
import matplotlib.pyplot as plt
import matplotlib
import numpy as np

# 设置中文字体
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False


def normalize_filename(filename: str) -> str:
    """
    标准化文件名：仅去除扩展名，统一大小写

    Args:
        filename: 原始文件名

    Returns:
        标准化后的文件名（无扩展名，全大写）
    """
    # 仅去除扩展名
    name = Path(filename).stem

    # 统一转换为大写
    return name.upper()


def get_files_from_folder(folder_path: Path, is_folder_mode: bool = False) -> Dict[str, List[str]]:
    """
    获取文件夹中的所有文件名（去除扩展名）
    
    Args:
        folder_path: 文件夹路径
        is_folder_mode: 如果为True，则获取子文件夹名而不是文件名
        
    Returns:
        字典 {标准化文件名: [原始文件名列表]}
    """
    files_dict = {}
    
    if not folder_path.exists():
        return files_dict
    
    for item_path in folder_path.iterdir():
        # 跳过比例尺相关文件/文件夹
        if '比例尺' in item_path.name:
            continue
            
        # 根据模式选择文件或文件夹
        if is_folder_mode:
            if item_path.is_dir():
                normalized = normalize_filename(item_path.name)
                if normalized not in files_dict:
                    files_dict[normalized] = []
                files_dict[normalized].append(item_path.name)
        else:
            if item_path.is_file():
                normalized = normalize_filename(item_path.name)
                if normalized not in files_dict:
                    files_dict[normalized] = []
                files_dict[normalized].append(item_path.name)
    
    return files_dict


def compare_folders(
    folder1_path: str,
    folder2_path: str,
    folder3_path: str,
    folder1_name: str = "文件夹1",
    folder2_name: str = "文件夹2",
    folder3_name: str = "文件夹3"
) -> Dict:
    """
    比对三个文件夹中的文件
    
    Args:
        folder1_path: 第一个文件夹路径
        folder2_path: 第二个文件夹路径
        folder3_path: 第三个文件夹路径
        folder1_name: 第一个文件夹的显示名称
        folder2_name: 第二个文件夹的显示名称
        folder3_name: 第三个文件夹的显示名称
        
    Returns:
        比对结果字典
    """
    folder1 = Path(folder1_path)
    folder2 = Path(folder2_path)
    folder3 = Path(folder3_path)
    
    # 获取各文件夹的文件
    # 前两个文件夹是文件，第三个文件夹（高速摄像）是子文件夹
    files1 = get_files_from_folder(folder1, is_folder_mode=False)
    files2 = get_files_from_folder(folder2, is_folder_mode=False)
    files3 = get_files_from_folder(folder3, is_folder_mode=True)  # 高速摄像文件夹包含子文件夹
    
    # 获取所有唯一的标准化文件名
    all_files = set(files1.keys()) | set(files2.keys()) | set(files3.keys())
    
    # 分类文件
    only_in_1 = set(files1.keys()) - set(files2.keys()) - set(files3.keys())
    only_in_2 = set(files2.keys()) - set(files1.keys()) - set(files3.keys())
    only_in_3 = set(files3.keys()) - set(files1.keys()) - set(files2.keys())
    
    in_1_and_2 = (set(files1.keys()) & set(files2.keys())) - set(files3.keys())
    in_1_and_3 = (set(files1.keys()) & set(files3.keys())) - set(files2.keys())
    in_2_and_3 = (set(files2.keys()) & set(files3.keys())) - set(files1.keys())
    
    in_all_three = set(files1.keys()) & set(files2.keys()) & set(files3.keys())
    
    return {
        'all_files': all_files,
        'files1': files1, 'files2': files2, 'files3': files3,
        'folder1_path': folder1, 'folder2_path': folder2, 'folder3_path': folder3,
        'only_in_1': only_in_1, 'only_in_2': only_in_2, 'only_in_3': only_in_3,
        'in_1_and_2': in_1_and_2, 'in_1_and_3': in_1_and_3, 'in_2_and_3': in_2_and_3,
        'in_all_three': in_all_three,
        'folder1_name': folder1_name,
        'folder2_name': folder2_name,
        'folder3_name': folder3_name
    }

def copy_common_files(results: Dict, target_base_dir: str):
    """
    将三者均有的文件/文件夹复制到指定目录
    """
    target_root = Path(target_base_dir)
    common_names = results['in_all_three']
    
    if not common_names:
        print("没有发现三者共有的文件，跳过复制。")
        return

    # 定义子目录映射
    sub_dirs = {
        'folder1': target_root / results['folder1_name'],
        'folder2': target_root / results['folder2_name'],
        'folder3': target_root / results['folder3_name']
    }

    # 创建目标子目录
    for d in sub_dirs.values():
        d.mkdir(parents=True, exist_ok=True)

    print(f"\n正在开始复制共有文件到: {target_base_dir} ...")
    
    copy_count = 0
    for name in common_names:
        # 复制文件夹1中的文件
        for origin_name in results['files1'][name]:
            src = results['folder1_path'] / origin_name
            shutil.copy2(src, sub_dirs['folder1'] / origin_name)
        
        # 复制文件夹2中的文件
        for origin_name in results['files2'][name]:
            src = results['folder2_path'] / origin_name
            shutil.copy2(src, sub_dirs['folder2'] / origin_name)
            
        # 复制文件夹3中的子文件夹 (高速摄像模式)
        for origin_name in results['files3'][name]:
            src = results['folder3_path'] / origin_name
            dst = sub_dirs['folder3'] / origin_name
            if dst.exists():
                shutil.rmtree(dst) # 如果已存在则删除旧的，确保拷贝最新
            shutil.copytree(src, dst)
        
        copy_count += 1
        if copy_count % 10 == 0:
            print(f"已处理 {copy_count}/{len(common_names)} 组文件...")

    print(f"复制完成！共复制了 {copy_count} 组共有数据。")

def create_visualization(results: Dict, output_path: Path):
    """
    创建可视化图表
    
    Args:
        results: 比对结果
        output_path: 输出图片路径
    """
    # 准备数据
    categories = [
        '三个文件夹都有',
        f'仅在{results["folder1_name"]}',
        f'仅在{results["folder2_name"]}',
        f'仅在{results["folder3_name"]}',
        f'{results["folder1_name"]}和{results["folder2_name"]}',
        f'{results["folder1_name"]}和{results["folder3_name"]}',
        f'{results["folder2_name"]}和{results["folder3_name"]}'
    ]
    
    counts = [
        len(results['in_all_three']),
        len(results['only_in_1']),
        len(results['only_in_2']),
        len(results['only_in_3']),
        len(results['in_1_and_2']),
        len(results['in_1_and_3']),
        len(results['in_2_and_3'])
    ]
    
    # 创建图表
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    # 左图：柱状图
    colors = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#3498db', '#1abc9c', '#34495e']
    bars = ax1.barh(categories, counts, color=colors)
    ax1.set_xlabel('文件数量', fontsize=12)
    ax1.set_title('文件分布统计', fontsize=14, fontweight='bold')
    ax1.grid(axis='x', alpha=0.3)
    
    # 在柱状图上添加数值标签
    for i, (bar, count) in enumerate(zip(bars, counts)):
        if count > 0:
            ax1.text(count + 0.5, i, str(count), va='center', fontsize=10)
    
    # 右图：韦恩图风格（使用饼图展示）
    # 计算各部分占比
    total = sum(counts)
    if total > 0:
        # 只显示有数据的部分
        non_zero_categories = []
        non_zero_counts = []
        non_zero_colors = []
        
        for cat, cnt, col in zip(categories, counts, colors):
            if cnt > 0:
                non_zero_categories.append(f"{cat}\n({cnt})")
                non_zero_counts.append(cnt)
                non_zero_colors.append(col)
        
        if non_zero_counts:
            wedges, texts, autotexts = ax2.pie(
                non_zero_counts,
                labels=non_zero_categories,
                colors=non_zero_colors,
                autopct='%1.1f%%',
                startangle=90
            )
            
            # 调整文字大小
            for text in texts:
                text.set_fontsize(9)
            for autotext in autotexts:
                autotext.set_fontsize(9)
                autotext.set_color('white')
                autotext.set_fontweight('bold')
    
    ax2.set_title('文件分布比例', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"可视化图表已保存到: {output_path}")
    plt.close()


def print_comparison_results(results: Dict):
    """
    打印比对结果
    
    Args:
        results: 比对结果
    """
    print("=" * 80)
    print("文件比对结果")
    print("=" * 80)
    print(f"\n文件夹1: {results['folder1_name']} - {len(results['files1'])} 个文件")
    print(f"文件夹2: {results['folder2_name']} - {len(results['files2'])} 个文件")
    print(f"文件夹3: {results['folder3_name']} - {len(results['files3'])} 个文件")
    print(f"总计唯一文件: {len(results['all_files'])} 个")
    
    print("\n" + "-" * 80)
    print("文件分布情况:")
    print("-" * 80)
    print(f"三个文件夹都有: {len(results['in_all_three'])} 个")
    print(f"仅在 {results['folder1_name']}: {len(results['only_in_1'])} 个")
    print(f"仅在 {results['folder2_name']}: {len(results['only_in_2'])} 个")
    print(f"仅在 {results['folder3_name']}: {len(results['only_in_3'])} 个")
    print(f"{results['folder1_name']} 和 {results['folder2_name']}: {len(results['in_1_and_2'])} 个")
    print(f"{results['folder1_name']} 和 {results['folder3_name']}: {len(results['in_1_and_3'])} 个")
    print(f"{results['folder2_name']} 和 {results['folder3_name']}: {len(results['in_2_and_3'])} 个")
    
    # 打印详细信息
    if results['in_all_three']:
        print("\n" + "-" * 80)
        print("三个文件夹都有的文件:")
        print("-" * 80)
        for name in sorted(results['in_all_three']):
            print(f"  {name}")
            print(f"    - {results['folder1_name']}: {', '.join(results['files1'][name])}")
            print(f"    - {results['folder2_name']}: {', '.join(results['files2'][name])}")
            print(f"    - {results['folder3_name']}: {', '.join(results['files3'][name])}")
    
    if results['only_in_1']:
        print("\n" + "-" * 80)
        print(f"仅在 {results['folder1_name']} 的文件:")
        print("-" * 80)
        for name in sorted(results['only_in_1']):
            print(f"  {name}: {', '.join(results['files1'][name])}")
    
    if results['only_in_2']:
        print("\n" + "-" * 80)
        print(f"仅在 {results['folder2_name']} 的文件:")
        print("-" * 80)
        for name in sorted(results['only_in_2']):
            print(f"  {name}: {', '.join(results['files2'][name])}")
    
    if results['only_in_3']:
        print("\n" + "-" * 80)
        print(f"仅在 {results['folder3_name']} 的文件:")
        print("-" * 80)
        for name in sorted(results['only_in_3']):
            print(f"  {name}: {', '.join(results['files3'][name])}")


# def main():
#     """主函数"""
#     # 配置路径
#     base_path = Path(r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据")
    
#     folder1_path = base_path / "光强信号_第一列 可见光_第二列 反射光_第三列_红外光"
#     folder2_path = base_path / "光谱信号"
#     folder3_path = base_path / "高速摄像"
    
#     # 比对文件夹
#     results = compare_folders(
#         folder1_path=str(folder1_path),
#         folder2_path=str(folder2_path),
#         folder3_path=str(folder3_path),
#         folder1_name="光强信号",
#         folder2_name="光谱信号",
#         folder3_name="高速摄像"
#     )
    
#     # 打印结果
#     print_comparison_results(results)
    
#     # 创建可视化图表
#     output_dir = Path(__file__).parent
#     output_image = output_dir / "文件夹比对结果.png"
#     create_visualization(results, output_image)
    
#     # 保存详细结果到文本文件
#     output_txt = output_dir / "文件夹比对结果.txt"
#     with open(output_txt, 'w', encoding='utf-8') as f:
#         f.write("=" * 80 + "\n")
#         f.write("文件比对结果\n")
#         f.write("=" * 80 + "\n")
#         f.write(f"\n文件夹1: {results['folder1_name']} - {len(results['files1'])} 个文件\n")
#         f.write(f"文件夹2: {results['folder2_name']} - {len(results['files2'])} 个文件\n")
#         f.write(f"文件夹3: {results['folder3_name']} - {len(results['files3'])} 个文件\n")
#         f.write(f"总计唯一文件: {len(results['all_files'])} 个\n")
        
#         f.write("\n" + "-" * 80 + "\n")
#         f.write("文件分布情况:\n")
#         f.write("-" * 80 + "\n")
#         f.write(f"三个文件夹都有: {len(results['in_all_three'])} 个\n")
#         f.write(f"仅在 {results['folder1_name']}: {len(results['only_in_1'])} 个\n")
#         f.write(f"仅在 {results['folder2_name']}: {len(results['only_in_2'])} 个\n")
#         f.write(f"仅在 {results['folder3_name']}: {len(results['only_in_3'])} 个\n")
#         f.write(f"{results['folder1_name']} 和 {results['folder2_name']}: {len(results['in_1_and_2'])} 个\n")
#         f.write(f"{results['folder1_name']} 和 {results['folder3_name']}: {len(results['in_1_and_3'])} 个\n")
#         f.write(f"{results['folder2_name']} 和 {results['folder3_name']}: {len(results['in_2_and_3'])} 个\n")
        
#         # 详细列表
#         if results['in_all_three']:
#             f.write("\n" + "-" * 80 + "\n")
#             f.write("三个文件夹都有的文件:\n")
#             f.write("-" * 80 + "\n")
#             for name in sorted(results['in_all_three']):
#                 f.write(f"{name}\n")
#                 f.write(f"  - {results['folder1_name']}: {', '.join(results['files1'][name])}\n")
#                 f.write(f"  - {results['folder2_name']}: {', '.join(results['files2'][name])}\n")
#                 f.write(f"  - {results['folder3_name']}: {', '.join(results['files3'][name])}\n")
    
#     print(f"\n详细结果已保存到: {output_txt}")

def main():
    """主函数"""
    # 配置路径
    base_path = Path(r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据\3mm复合材料和铝合金焊接数据")
    
    folder1_path = base_path / "光强信号_第一列 可见光_第二列 反射光_第三列_红外光"
    folder2_path = base_path / "光谱信号"
    folder3_path = base_path / "高速摄像"
    
    # 比对文件夹
    results = compare_folders(
        folder1_path=str(folder1_path),
        folder2_path=str(folder2_path),
        folder3_path=str(folder3_path),
        folder1_name="光强信号",
        folder2_name="光谱信号",
        folder3_name="高速摄像"
    )
    
    # 打印到控制台
    print_comparison_results(results)
    
    # 创建可视化图表
    output_dir = Path(__file__).parent
    output_image = output_dir / "文件夹比对结果.png"
    create_visualization(results, output_image)
    
    # 保存详细结果到文本文件 (完整导出所有分类)
    output_txt = output_dir / "文件夹比对结果.txt"
    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write("=" * 80 + "\n")
        f.write("文件比对报告 (完整版)\n")
        f.write("=" * 80 + "\n")
        f.write(f"\n文件夹1: {results['folder1_name']} - {len(results['files1'])} 个文件\n")
        f.write(f"文件夹2: {results['folder2_name']} - {len(results['files2'])} 个文件\n")
        f.write(f"文件夹3: {results['folder3_name']} - {len(results['files3'])} 个子文件夹\n")
        f.write(f"总计唯一文件名（去除后缀）: {len(results['all_files'])} 个\n")
        
        f.write("\n" + "-" * 80 + "\n")
        f.write("1. 文件分布汇总统计:\n")
        f.write("-" * 80 + "\n")
        f.write(f"三个文件夹共有: {len(results['in_all_three'])} 个\n")
        f.write(f"仅在 {results['folder1_name']} 中: {len(results['only_in_1'])} 个\n")
        f.write(f"仅在 {results['folder2_name']} 中: {len(results['only_in_2'])} 个\n")
        f.write(f"仅在 {results['folder3_name']} 中: {len(results['only_in_3'])} 个\n")
        f.write(f"{results['folder1_name']} 和 {results['folder2_name']} 共有: {len(results['in_1_and_2'])} 个\n")
        f.write(f"{results['folder1_name']} 和 {results['folder3_name']} 共有: {len(results['in_1_and_3'])} 个\n")
        f.write(f"{results['folder2_name']} 和 {results['folder3_name']} 共有: {len(results['in_2_and_3'])} 个\n")
        
        # --- 详细列表输出 ---
        
        # 三个都有
        if results['in_all_three']:
            f.write("\n" + "-" * 80 + "\n")
            f.write("2. [三者共有] 文件详细清单:\n")
            f.write("-" * 80 + "\n")
            for name in sorted(results['in_all_three']):
                f.write(f"【{name}】\n")
                f.write(f"  - {results['folder1_name']}: {', '.join(results['files1'][name])}\n")
                f.write(f"  - {results['folder2_name']}: {', '.join(results['files2'][name])}\n")
                f.write(f"  - {results['folder3_name']}: {', '.join(results['files3'][name])}\n")

        # 仅在1
        if results['only_in_1']:
            f.write("\n" + "-" * 80 + "\n")
            f.write(f"3. [仅存在于 {results['folder1_name']}] 的文件:\n")
            f.write("-" * 80 + "\n")
            for name in sorted(results['only_in_1']):
                f.write(f"{name} ({', '.join(results['files1'][name])})\n")

        # 仅在2
        if results['only_in_2']:
            f.write("\n" + "-" * 80 + "\n")
            f.write(f"4. [仅存在于 {results['folder2_name']}] 的文件:\n")
            f.write("-" * 80 + "\n")
            for name in sorted(results['only_in_2']):
                f.write(f"{name} ({', '.join(results['files2'][name])})\n")

        # 仅在3
        if results['only_in_3']:
            f.write("\n" + "-" * 80 + "\n")
            f.write(f"5. [仅存在于 {results['folder3_name']}] 的文件:\n")
            f.write("-" * 80 + "\n")
            for name in sorted(results['only_in_3']):
                f.write(f"{name} ({', '.join(results['files3'][name])})\n")

        # 两两共有情况说明
        for pair_name, pair_key in [
            (f"{results['folder1_name']} & {results['folder2_name']}", 'in_1_and_2'),
            (f"{results['folder1_name']} & {results['folder3_name']}", 'in_1_and_3'),
            (f"{results['folder2_name']} & {results['folder3_name']}", 'in_2_and_3')
        ]:
            if results[pair_key]:
                f.write("\n" + "-" * 80 + "\n")
                f.write(f"两者共有清单: {pair_name}\n")
                f.write("-" * 80 + "\n")
                for name in sorted(results[pair_key]):
                    f.write(f"{name}\n")

    # 5. 执行复制共有文件功能
    target_copy_dir = r"E:\value_code\Metal_welding\data\3mm复合材料和铝合金焊接数据_三者均有"
    copy_common_files(results, target_copy_dir)

    print(f"\n任务全部完成！")
    print(f"报告及图表在: {output_dir}")
    print(f"共有文件已分类拷贝至: {target_copy_dir}")

if __name__ == "__main__":
    main()

