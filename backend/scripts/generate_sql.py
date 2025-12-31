"""
初始化数据库脚本生成器
读取CSV/Excel文件，自动生成建表SQL
"""

import os
import sys
import pandas as pd

# 批次配置
BATCHES = {
    "batch_1": "exp_data_batch_1",
    "batch_2": "exp_data_batch_2",
    "batch_3": "exp_data_batch_3",
    "batch_4": "exp_data_batch_4"
}


def read_excel(file_path: str, sheet_name=0):
    """读取Excel文件"""
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return None


def analyze_columns(df: pd.DataFrame):
    """分析列并分类"""
    columns = df.columns.tolist()
    categories = {
        "物性": [],
        "工艺": [],
        "状态": [],
        "性能": [],
        "其他": []
    }
    
    category_keywords = {
        "物性": ["材料", "成分", "基体", "SiC", "体积", "密度", "实验编号"],
        "工艺": ["激光", "功率", "焊接", "速度", "离焦", "保护气体", "流量"],
        "状态": ["温度", "熔池", "图像", "传感器", "信号"],
        "性能": ["拉伸", "强度", "硬度", "焊缝", "宽度", "熔深"]
    }
    
    for col in columns:
        categorized = False
        for category, keywords in category_keywords.items():
            if any(keyword in col for keyword in keywords):
                categories[category].append(col)
                categorized = True
                break
        if not categorized:
            categories["其他"].append(col)
    
    return {k: v for k, v in categories.items() if v}


def generate_create_table_sql(df: pd.DataFrame, table_name: str):
    """生成建表SQL"""
    columns = df.columns.tolist()
    
    sql_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
    sql_parts.append("    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID（自增主键）',")
    
    # 所有CSV字段都不设为主键或唯一索引
    for col in columns:
        sql_parts.append(f"    `{col}` VARCHAR(255) COMMENT '{col}',")
    
    sql_parts.append("    data_source ENUM('experiment', 'literature') NOT NULL DEFAULT 'experiment' COMMENT '数据来源',")
    sql_parts.append("    related_files JSON COMMENT '关联文件列表',")
    sql_parts.append("    notes TEXT COMMENT '备注信息',")
    sql_parts.append("    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',")
    sql_parts.append("    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',")
    sql_parts.append("    created_by VARCHAR(50) COMMENT '创建人',")
    sql_parts.append("    updated_by VARCHAR(50) COMMENT '更新人',")
    
    # 只添加时间索引，不对CSV字段建索引
    sql_parts.append("    INDEX idx_created_at (created_at)")
    
    sql_parts.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{table_name}';")
    
    return "\n".join(sql_parts)


def generate_sql_for_batch(batch_id: str, file_path: str, output_dir: str = "../../sql"):
    """
    为指定批次生成SQL文件
    
    Args:
        batch_id: 批次ID (batch_1, batch_2, etc.)
        file_path: Excel/CSV文件路径
        output_dir: 输出目录
    """
    print(f"\n处理批次: {batch_id}")
    print(f"文件路径: {file_path}")
    
    df = read_excel(file_path)
    
    if df is None:
        print(f"✗ 读取文件失败: {file_path}")
        return False
    
    print(f"✓ 成功读取 {len(df)} 行数据")
    print(f"✓ 共 {len(df.columns)} 列")
    
    # 显示列信息
    print(f"\n列名:")
    for i, col in enumerate(df.columns, 1):
        print(f"  {i}. {col}")
    
    # 分析列分类
    categories = analyze_columns(df)
    print(f"\n列分类:")
    for category, cols in categories.items():
        print(f"  {category}: {len(cols)}个")
        for col in cols:
            print(f"    - {col}")
    
    # 生成建表SQL
    table_name = BATCHES[batch_id]
    sql = generate_create_table_sql(df, table_name)
    
    # 保存SQL文件
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"init_{batch_id}.sql")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"-- {batch_id} 建表SQL\n")
        f.write(f"-- 自动生成时间: 2025-12-18\n")
        f.write(f"-- 数据源: {os.path.basename(file_path)}\n\n")
        f.write(sql)
        f.write("\n")
    
    print(f"\n✓ SQL文件已生成: {output_file}")
    return True


def main():
    """主函数"""
    print("=" * 60)
    print("数据库初始化脚本生成器")
    print("=" * 60)
    
    # 批次1
    batch_1_file = "../../data/batch_1/625试验数据_修改过后.xlsx"
    if os.path.exists(batch_1_file):
        generate_sql_for_batch("batch_1", batch_1_file)
    else:
        print(f"✗ 文件不存在: {batch_1_file}")
    
    print("\n" + "=" * 60)
    print("完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()
