"""
导入Excel数据到MySQL数据库

本脚本用于批量导入实验数据到数据库，支持重复检测和错误处理。

功能：
1. 读取Excel/CSV文件
2. 清洗和验证数据
3. 检测重复记录（所有字段完全相同）
4. 批量导入到MySQL
5. 显示导入统计和错误详情

使用方式：
    cd backend/scripts
    # 修改脚本中的file_path和table_name
    python import_data.py
"""

import pymysql
import pandas as pd
from pathlib import Path
import sys

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from config import settings

# 初始化日志记录器
logger = get_logger(__name__)


def read_excel_file(file_path: str):
    """
    读取Excel文件并返回DataFrame
    
    功能说明：
    1. 使用pandas读取Excel文件（支持.xlsx和.xls格式）
    2. 自动识别第一个sheet
    3. 显示读取的行数和列数统计信息
    4. 错误处理：文件不存在、格式错误等
    5. 返回pandas DataFrame对象供后续处理
    
    Args:
        file_path (str): Excel文件的完整路径
    
    Returns:
        pd.DataFrame: 成功返回DataFrame对象，失败返回None
    
    Raises:
        Exception: 读取失败时记录错误日志
    
    使用示例：
        df = read_excel_file("data/batch_1/实验数据.xlsx")
        if df is not None:
            logger.info(f"成功读取 {len(df)} 行数据")
    """
    try:
        logger.info(f"正在读取Excel文件: {file_path}")
        df = pd.read_excel(file_path)
        
        logger.info(f"✓ 成功读取Excel文件")
        logger.info(f"  行数: {len(df)}")
        logger.info(f"  列数: {len(df.columns)}")
        logger.debug(f"  列名: {', '.join(df.columns.tolist())}")
        
        return df
    except Exception as e:
        logger.error(f"✗ 读取Excel失败: {str(e)}", exc_info=True)
        return None


def clean_value(value):
    """
    清洗数据值，统一处理空值
    
    功能说明：
    1. 检查pandas的NaN值（pd.isna）
    2. 转换为字符串并去除首尾空格
    3. 识别多种空值表示（空字符串、N/A、null等）
    4. 统一转换为None（数据库NULL）
    5. 保证数据一致性和查询准确性
    
    Args:
        value: 任意类型的数据值
    
    Returns:
        str | None: 清洗后的字符串值，或None（表示NULL）
    
    使用示例：
        cleaned = clean_value("  N/A  ")  # 返回: None
        cleaned = clean_value("有效数据")   # 返回: "有效数据"
        cleaned = clean_value(pd.NaT)      # 返回: None
    """
    # 处理pandas的NaN值
    if pd.isna(value):
        return None
    
    # 转换为字符串并去除空格
    value_str = str(value).strip()
    
    # 定义空值列表（各种空值的表示方法）
    null_values = [
        "", " ", "N/A", "n/a", "NA", "na", "-", 
        "unknown", "Unknown", "UNKNOWN", 
        "null", "Null", "NULL", "none", "None"
    ]
    
    # 检查是否为空值
    if value_str in null_values:
        return None
    
    return value_str


def import_data_to_mysql(df: pd.DataFrame, table_name: str, batch_size: int = 50):
    """
    将清洗后的DataFrame数据导入到MySQL数据库
    
    功能说明：
    1. 建立数据库连接并验证目标表是否存在
    2. 自动获取表结构，排除自增ID和审计字段（created_at等）
    3. 匹配DataFrame列名与数据库字段名
    4. 逐行进行重复性检查（全字段匹配），避免重复导入
    5. 批量执行插入操作并记录成功、失败和重复的数量
    6. 事务处理：确保数据一致性，并在完成后提交
    
    Args:
        df (pd.DataFrame): 包含待导入数据的DataFrame
        table_name (str): 目标数据库表名
        batch_size (int, optional): 批量处理的大小. Defaults to 50.
    
    Returns:
        tuple: (success_count, failed_count) 成功和失败的行数
    
    Raises:
        Exception: 数据库连接或表验证失败时抛出异常
    """
    try:
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        logger.info(f"✓ 数据库连接成功 (database={settings.MYSQL_DATABASE})")
        
        cursor = connection.cursor()
        
        # 调试：验证数据库和表
        cursor.execute("SELECT DATABASE()")
        current_db = cursor.fetchone()[0]
        logger.info(f"  当前数据库: {current_db}")
        
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        logger.debug(f"  可用的表: {tables}")
        
        if table_name not in tables:
            logger.error(f"✗ 表 '{table_name}' 不存在于数据库 '{current_db}' 中")
            raise Exception(f"表 '{table_name}' 不存在")
        
        # 获取表的所有列（排除自增id和审计字段）
        cursor.execute("SHOW COLUMNS FROM " + table_name)
        all_columns = [row[0] for row in cursor.fetchall()]
        
        # 排除不需要插入的字段
        exclude_fields = ['id', 'data_source', 'related_files', 'notes', 
                         'created_at', 'updated_at', 'created_by', 'updated_by']
        data_columns = [col for col in all_columns if col not in exclude_fields]
        
        # 确保DataFrame中的列和数据库列匹配
        df_columns = df.columns.tolist()
        valid_columns = [col for col in data_columns if col in df_columns]
        
        logger.info(f"开始导入数据到表: {table_name}")
        logger.info(f"  匹配字段数: {len(valid_columns)}")
        logger.info(f"  待处理行数: {len(df)}")
        
        # 构建INSERT语句 - 将列名中的%转义为%%，避免PyMySQL误解析
        placeholders = ', '.join(['%s'] * len(valid_columns))
        # 转义列名中的百分号，并用反引号包裹
        escaped_columns = ['`' + col.replace('%', '%%') + '`' for col in valid_columns]
        column_names = ', '.join(escaped_columns)
        insert_sql = "INSERT INTO " + table_name + " (" + column_names + ") VALUES (" + placeholders + ")"
        
        # 批量插入（带重复检查）
        success_count = 0
        failed_count = 0
        duplicate_count = 0
        failed_rows = []
        
        for index, row in df.iterrows():
            try:
                # 清洗数据
                values = [clean_value(row[col]) for col in valid_columns]
                
                # 检查是否存在完全相同的记录
                check_conditions = ' AND '.join([
                    f"(`{col.replace('%', '%%')}` = %s OR (`{col.replace('%', '%%')}` IS NULL AND %s IS NULL))"
                    for col in valid_columns
                ])
                check_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {check_conditions}"
                # 为每个字段准备两个值（用于IS NULL检查）
                check_values = []
                for val in values:
                    check_values.extend([val, val])
                
                cursor.execute(check_sql, tuple(check_values))
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    duplicate_count += 1
                    if duplicate_count <= 3:
                        logger.debug(f"  ⊙ 第{index + 1}行已存在，跳过")
                    continue
                
                # 执行插入
                cursor.execute(insert_sql, tuple(values))
                success_count += 1
                
                # 显示进度
                if (index + 1) % 50 == 0:
                    logger.info(f"  进度: {index + 1}/{len(df)} (成功:{success_count}, 重复:{duplicate_count})")
                
            except Exception as e:
                failed_count += 1
                failed_rows.append({'row': index + 1, 'error': str(e)})
                if failed_count <= 5:
                    logger.warning(f"  ✗ 第{index + 1}行导入失败: {str(e)}")
        
        # 提交事务
        connection.commit()
        
        logger.info("=" * 40)
        logger.info(f"导入完成统计:")
        logger.info(f"✓ 成功插入: {success_count} 行")
        logger.info(f"⊙ 重复跳过: {duplicate_count} 行")
        logger.info(f"✗ 失败: {failed_count} 行")
        logger.info("=" * 40)
        
        if failed_count > 0:
            logger.error(f"失败详情 (前5条):")
            for item in failed_rows[:5]:
                logger.error(f"  第{item['row']}行: {item['error']}")
        
        # 验证导入结果
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        total = cursor.fetchone()[0]
        logger.info(f"数据库中当前总记录数: {total}")
        
        cursor.close()
        connection.close()
        
        return success_count, failed_count
        
    except Exception as e:
        logger.error(f"✗ 导入过程发生严重错误: {e}", exc_info=True)
        return 0, 0


def main():
    """
    数据导入脚本入口函数
    
    功能说明：
    1. 设置待导入的Excel文件路径和目标数据库表名
    2. 检查文件是否存在
    3. 调用read_excel_file读取数据
    4. 调用import_data_to_mysql执行导入
    5. 输出最终执行结果报告
    """
    logger.info("=" * 60)
    logger.info("开始执行数据导入任务")
    logger.info("=" * 60)
    
    # 批次1的Excel文件路径
    excel_file = "../../data/batch_1/625试验数据_修改过后.xlsx"
    abs_path = Path(__file__).parent / excel_file
    
    if not abs_path.exists():
        logger.error(f"✗ 文件不存在: {abs_path}")
        return
    
    # 读取Excel
    df = read_excel_file(str(abs_path))
    if df is None:
        return
    
    # 导入到数据库
    table_name = "exp_data_batch_1"
    success, failed = import_data_to_mysql(df, table_name)
    
    if failed == 0:
        logger.info("✓ 任务圆满完成: 所有数据已成功导入")
    else:
        logger.warning(f"⚠ 任务完成但存在错误: {failed} 行导入失败")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
