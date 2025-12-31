"""
数据库初始化脚本

本脚本用于执行SQL初始化文件，创建系统表并初始化基础数据。
支持执行多个SQL文件，并提供详细的执行进度和错误报告。

功能：
1. 建立数据库连接
2. 读取并解析SQL文件（支持多语句分割）
3. 自动过滤SQL注释
4. 批量执行SQL语句并提交事务
5. 验证初始化后的表结构
"""

import pymysql
import os
import sys
from pathlib import Path

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from config import settings

# 初始化日志记录器
logger = get_logger(__name__)


def get_db_connection():
    """
    创建并返回数据库连接
    
    功能说明：
    1. 使用预设的配置连接MySQL数据库
    2. 验证连接是否成功
    3. 检查当前连接的数据库名称
    4. 异常处理：捕获并记录连接失败的具体原因
    
    Returns:
        pymysql.connections.Connection: 成功返回连接对象，失败返回None
    """
    try:
        # 1. 第一步：先不指定数据库名，只连接服务器
        logger.info(f"正在尝试连接 MySQL 服务器: {settings.MYSQL_HOST}...")
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 2. 第二步：动态创建数据库
        db_name = settings.MYSQL_DATABASE
        logger.info(f"检查并创建数据库: {db_name}")
        # 使用 f-string 注入库名是安全的，因为这是从配置中读取的
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        # 3. 第三步：切换到该数据库
        connection.select_db(db_name)
        logger.info(f"✓ 成功进入数据库: {db_name}")
        
        cursor.close()
        return connection

    except Exception as e:
        if connection:
            connection.close()
        logger.error(f"✗ 数据库初始化连接失败: {e}", exc_info=True)
        return None


def execute_sql_file(connection, sql_file_path: str):
    """
    读取并执行指定的SQL文件
    
    功能说明：
    1. 读取SQL文件内容
    2. 预处理：移除单行注释（--）
    3. 分割：按分号（;）将内容分割为独立的SQL语句
    4. 执行：逐条执行SQL语句，并跳过空语句
    5. 容错：忽略重复键错误（Duplicate entry），记录其他警告
    6. 事务：执行完成后统一提交
    
    Args:
        connection: 数据库连接对象
        sql_file_path (str): SQL文件的绝对路径
    
    Returns:
        bool: 执行成功返回True，发生严重错误返回False
    """
    try:
        if not os.path.exists(sql_file_path):
            logger.error(f"✗ SQL文件不存在: {sql_file_path}")
            return False
            
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 移除注释行
        lines = sql_content.split('\n')
        clean_lines = [line for line in lines if not line.strip().startswith('--')]
        clean_sql = '\n'.join(clean_lines)
        
        # 分割SQL语句
        sql_statements = [stmt.strip() for stmt in clean_sql.split(';') if stmt.strip()]
        
        cursor = connection.cursor()
        executed_count = 0
        error_count = 0
        
        logger.info(f"正在执行SQL文件: {os.path.basename(sql_file_path)}")
        
        for statement in sql_statements:
            if statement:
                try:
                    cursor.execute(statement)
                    executed_count += 1
                except Exception as e:
                    # 忽略重复键错误
                    if 'Duplicate entry' not in str(e):
                        logger.warning(f"  警告 (语句 {executed_count + 1}): {e}")
                        logger.debug(f"  失败语句: {statement[:200]}...")
                        error_count += 1
        
        connection.commit()
        cursor.close()
        
        logger.info(f"✓ SQL文件执行完成: {os.path.basename(sql_file_path)}")
        logger.info(f"  成功执行: {executed_count} 条语句")
        if error_count > 0:
            logger.warning(f"  忽略错误: {error_count} 条")
            
        return True
    except Exception as e:
        logger.error(f"✗ SQL文件执行失败: {e}", exc_info=True)
        return False


def main():
    """
    数据库初始化主函数
    
    功能说明：
    1. 确定SQL文件所在目录
    2. 建立数据库连接
    3. 按顺序执行初始化SQL文件（init_database.sql等）
    4. 验证并列出数据库中当前所有的表
    5. 确保连接在完成后正确关闭
    """
    logger.info("=" * 60)
    logger.info("开始初始化数据库结构")
    logger.info("=" * 60)
    
    # 获取SQL目录
    sql_dir = Path(__file__).parent.parent.parent / 'sql'
    
    # 连接数据库
    conn = get_db_connection()
    if not conn:
        logger.error("✗ 初始化终止: 无法建立数据库连接")
        return
    
    try:
        # 1. 执行系统表初始化
        logger.info("步骤 1: 初始化系统表结构...")
        init_db_sql = sql_dir / 'init_database.sql'
        execute_sql_file(conn, str(init_db_sql))
        
        # 2. 验证表创建结果
        logger.info("步骤 2: 验证表结构...")
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        
        logger.info(f"当前数据库中的表 ({len(tables)}个):")
        for table in sorted(tables):
            logger.info(f"  - {table}")

        # 3. 同步/清理元数据
        logger.info("步骤 3: 正在同步元数据配置文件...")
        from cleanup_metadata import cleanup_metadata
        if cleanup_metadata:
            cleanup_metadata()
            logger.info("✓ dataset_metadata.json 已根据当前数据库状态完成清理")
        else:
            logger.warning("⚠ 未找到 cleanup_metadata 函数，请手动检查配置文件")
        
        logger.info("=" * 60)
        logger.info("✓ 数据库初始化任务圆满完成!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 初始化过程中发生未捕获的异常: {e}", exc_info=True)
    finally:
        conn.close()
        logger.info("✓ 数据库连接已安全关闭")


if __name__ == "__main__":
    main()
