"""
CSV处理服务模块
负责CSV文件读取、解析、验证和数据导入
"""

import pandas as pd
import os
import sys
from typing import List, Dict, Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


def detect_encoding(file_path: str) -> str:
    """
    检测文件编码
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 编码类型（utf-8或gbk）
    """
    # 尝试UTF-8
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return 'utf-8'
    except UnicodeDecodeError:
        pass
    
    # 尝试GBK
    try:
        with open(file_path, 'r', encoding='gbk') as f:
            f.read()
        return 'gbk'
    except UnicodeDecodeError:
        pass
    
    # 默认返回utf-8
    return 'utf-8'


def read_csv(file_path: str) -> pd.DataFrame:
    """
    读取CSV文件
    
    Args:
        file_path: CSV文件路径
        
    Returns:
        DataFrame: pandas数据框
    """
    encoding = detect_encoding(file_path)
    try:
        df = pd.read_csv(file_path, encoding=encoding)
        return df
    except Exception as e:
        print(f"读取CSV失败: {e}")
        return None


def read_excel(file_path: str, sheet_name: str = 0) -> pd.DataFrame:
    """
    读取Excel文件
    
    Args:
        file_path: Excel文件路径
        sheet_name: 工作表名称或索引，默认第一个
        
    Returns:
        DataFrame: pandas数据框
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return df
    except Exception as e:
        print(f"读取Excel失败: {e}")
        return None


def analyze_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    分析数据框的列，按照前缀分类
    
    Args:
        df: pandas数据框
        
    Returns:
        dict: 分类后的列字典 {category: [columns]}
    """
    columns = df.columns.tolist()
    categories = {
        "物性": [],
        "工艺": [],
        "状态": [],
        "性能": [],
        "其他": []
    }
    
    # 预定义的分类关键词
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
    
    # 移除空分类
    return {k: v for k, v in categories.items() if v}


def clean_value(value) -> str:
    """
    清洗数据值
    
    Args:
        value: 原始值
        
    Returns:
        str: 清洗后的值，如果是空值返回None
    """
    if pd.isna(value):
        return None
    
    value_str = str(value).strip()
    
    if value_str in settings.NULL_VALUES:
        return None
    
    return value_str


def dataframe_to_dict_list(df: pd.DataFrame) -> List[Dict]:
    """
    将DataFrame转换为字典列表，并清洗数据
    
    Args:
        df: pandas数据框
        
    Returns:
        list: 字典列表
    """
    records = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            record[col] = clean_value(row[col])
        records.append(record)
    
    return records


def generate_create_table_sql(df: pd.DataFrame, table_name: str, 
                               primary_key: str = "实验编号") -> str:
    """
    根据DataFrame生成建表SQL语句
    
    Args:
        df: pandas数据框
        table_name: 表名
        primary_key: 主键字段名，默认"实验编号"
        
    Returns:
        str: CREATE TABLE SQL语句
    """
    columns = df.columns.tolist()
    
    sql_parts = [f"CREATE TABLE IF NOT EXISTS {table_name} ("]
    sql_parts.append("    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '记录ID',")
    
    # 添加所有数据列
    for col in columns:
        if col == primary_key:
            sql_parts.append(f"    `{col}` VARCHAR(255) NOT NULL UNIQUE COMMENT '{col}',")
        else:
            sql_parts.append(f"    `{col}` VARCHAR(255) COMMENT '{col}',")
    
    # 添加附加字段
    sql_parts.append("    data_source ENUM('experiment', 'literature') NOT NULL DEFAULT 'experiment' COMMENT '数据来源',")
    sql_parts.append("    related_files JSON COMMENT '关联文件列表',")
    sql_parts.append("    notes TEXT COMMENT '备注信息',")
    sql_parts.append("    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',")
    sql_parts.append("    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',")
    sql_parts.append("    created_by VARCHAR(50) COMMENT '创建人',")
    sql_parts.append("    updated_by VARCHAR(50) COMMENT '更新人',")
    
    # 添加索引
    if primary_key in columns:
        sql_parts.append(f"    INDEX idx_experiment_no (`{primary_key}`),")
    sql_parts.append("    INDEX idx_created_at (created_at)")
    
    sql_parts.append(f") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='{table_name}';")
    
    return "\n".join(sql_parts)


def validate_csv_columns(df: pd.DataFrame, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    验证CSV列名
    
    Args:
        df: pandas数据框
        required_columns: 必需的列名列表
        
    Returns:
        tuple: (是否通过验证, 缺失的列名列表)
    """
    actual_columns = set(df.columns.tolist())
    required_columns_set = set(required_columns)
    
    missing_columns = list(required_columns_set - actual_columns)
    
    return len(missing_columns) == 0, missing_columns


def get_column_info(df: pd.DataFrame) -> Dict:
    """
    获取列的详细信息
    
    Args:
        df: pandas数据框
        
    Returns:
        dict: 列信息
    """
    info = {
        "total_columns": len(df.columns),
        "columns": df.columns.tolist(),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "null_counts": df.isnull().sum().to_dict(),
        "categories": analyze_columns(df)
    }
    
    return info


if __name__ == "__main__":
    # 测试读取Excel文件
    test_file = "../data/batch_1/625试验数据_修改过后.xlsx"
    if os.path.exists(test_file):
        print(f"读取文件: {test_file}")
        df = read_excel(test_file)
        
        if df is not None:
            print(f"\n总行数: {len(df)}")
            print(f"总列数: {len(df.columns)}")
            print(f"\n列名:")
            for i, col in enumerate(df.columns, 1):
                print(f"  {i}. {col}")
            
            print(f"\n列分类:")
            categories = analyze_columns(df)
            for category, cols in categories.items():
                print(f"\n{category} ({len(cols)}个):")
                for col in cols:
                    print(f"  - {col}")
            
            print(f"\n前5行数据:")
            print(df.head())
