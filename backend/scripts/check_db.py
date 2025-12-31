"""
检查数据库表和数据

本脚本用于验证数据库初始化结果，检查表结构和数据完整性。
适用于调试和故障排查。

功能：
1. 测试数据库连接状态
2. 列出所有表及其记录数
3. 显示指定表的字段结构
4. 输出数据库统计信息

使用方式：
    cd backend/scripts
    python check_db.py
"""

import pymysql
import sys
from pathlib import Path

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from config import settings

# 初始化日志记录器
logger = get_logger(__name__)


def check_database():
    """
    检查数据库完整状态
    
    功能说明：
    1. 连接到数据库并验证连接
    2. 列出所有表名及其记录数统计
    3. 显示exp_data_batch_1表的详细字段结构（示例）
    4. 输出系统表和数据表的完整信息
    5. 用于验证init_db.py和import_data.py的执行结果
    
    检查项目：
        - 数据库连接状态
        - 表数量统计
        - 记录数统计
        - 字段结构完整性
        - 字段类型正确性
    
    Returns:
        bool: 检查通过返回True，失败返回False
    
    Raises:
        Exception: 数据库操作失败时记录错误日志
    
    使用示例：
        if check_database():
            logger.info("数据库状态正常")
        else:
            logger.error("数据库存在问题，需要修复")
    """
    connection = None
    try:
        # 连接数据库
        logger.info("正在连接数据库...")
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        logger.info(f"✓ 数据库连接成功  数据库: {settings.MYSQL_DATABASE}  主机: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        
        cursor = connection.cursor()
        
        # 1. 检查所有表
        logger.info("=" * 60)
        logger.info("数据库中的所有表:")
        logger.info("=" * 60)
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        
        if not tables:
            logger.warning("✗ 数据库中没有表！请运行 init_db.py 初始化")
            return False
        
        # 统计每个表的记录数
        table_info = []
        for i, (table,) in enumerate(tables, 1):
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            table_info.append((table, count))
            logger.info(f"{i}. {table:30s} 记录数: {count}")
        
        total_tables = len(table_info)
        total_records = sum(count for _, count in table_info)
        logger.info("")
        logger.info(f"总计: {total_tables} 个表，{total_records} 条记录")
        
        # 2. 检查exp_data_batch_1表结构（示例）
        logger.info("")
        logger.info("=" * 60)
        logger.info("exp_data_batch_1 表结构:")
        logger.info("=" * 60)
        
        cursor.execute("DESCRIBE exp_data_batch_1")
        columns = cursor.fetchall()
        
        logger.info(f"字段总数: {len(columns)}")
        logger.info("")
        logger.info(f"{'字段名':<25s} {'类型':<20s} {'NULL':<6s} {'键':<6s}")
        logger.info("-" * 60)
        
        for col_name, col_type, null, key, default, extra in columns:
            key_str = f"[{key}]" if key else ""
            logger.info(f"{col_name:<25s} {col_type:<20s} {null:<6s} {key_str:<6s}")
        
        cursor.close()
        connection.close()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✓ 检查完成")
        logger.info("=" * 60)
        return True
        
    except Exception as e:
        logger.error(f"✗ 检查失败: {str(e)}", exc_info=True)
        return False
        
    finally:
        # 确保关闭连接
        if connection:
            try:
                connection.close()
                logger.debug("数据库连接已关闭")
            except:
                pass


def main():
    """
    主函数：执行数据库检查流程
    
    功能说明：
    1. 打印程序启动横幅
    2. 调用check_database()检查数据库状态
    3. 输出检查结果和建议
    4. 记录完整的执行日志
    
    Returns:
        None
    
    使用方式：
        cd backend/scripts
        python check_db.py
    """
    # 打印启动横幅
    logger.info("=" * 60)
    logger.info("数据库检查工具")
    logger.info("=" * 60)
    logger.info("")
    
    # 执行检查
    success = check_database()
    
    # 输出建议
    if not success:
        logger.info("")
        logger.info("建议操作:")
        logger.info("  1. 确认MySQL服务已启动")
        logger.info("  2. 运行 create_db.py 创建数据库")
        logger.info("  3. 运行 init_db.py 初始化表结构")
        logger.info("  4. 运行 import_data.py 导入数据")


if __name__ == "__main__":
    main()

