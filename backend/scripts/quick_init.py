"""
快速初始化脚本

本脚本用于一键完成数据库结构初始化和基础数据导入。
它按顺序执行系统表初始化 SQL 和批次数据初始化 SQL，适合开发环境快速重置。

功能：
1. 建立数据库连接
2. 执行 init_database.sql (系统表结构)
3. 执行 init_batch_1.sql (实验数据表结构)
4. 自动处理 SQL 注释和多语句分割
5. 验证最终生成的表结构
"""

import pymysql
import sys
import os
from pathlib import Path

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from config import settings

# 初始化日志记录器
logger = get_logger(__name__)


def run_quick_init():
    """
    执行快速初始化逻辑
    
    功能说明：
    1. 确定 SQL 文件路径（相对于脚本位置）
    2. 连接 MySQL 数据库
    3. 逐个读取并解析 SQL 文件
    4. 过滤注释并按分号分割语句
    5. 批量执行并提交事务
    6. 输出最终的表结构清单
    """
    logger.info("=" * 60)
    logger.info("开始执行快速初始化流程")
    logger.info("=" * 60)
    
    # 获取SQL目录
    script_dir = Path(__file__).parent
    sql_dir = script_dir.parent.parent / 'sql'
    
    # 连接数据库
    try:
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        logger.info(f"✓ 数据库连接成功 (database={settings.MYSQL_DATABASE})")
        
        cursor = conn.cursor()
        
        # 待执行的文件列表
        sql_files = [
            ('系统表结构', sql_dir / 'init_database.sql'),
            ('批次1数据表', sql_dir / 'init_batch_1.sql')
        ]
        
        for label, file_path in sql_files:
            if not file_path.exists():
                logger.error(f"✗ 文件不存在: {file_path}")
                continue
                
            logger.info(f"正在处理: {label} ({file_path.name})")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                sql_content = f.read()
            
            count = 0
            # 简单的SQL分割逻辑
            for statement in sql_content.split(';'):
                statement = statement.strip()
                # 跳过空行和注释
                if statement and not statement.startswith('--'):
                    try:
                        cursor.execute(statement)
                        count += 1
                        if 'CREATE TABLE' in statement.upper():
                            logger.debug(f"  创建表: {statement.split('(')[0].strip()}")
                    except Exception as e:
                        # 忽略重复创建错误，记录其他异常
                        if 'already exists' not in str(e).lower():
                            logger.warning(f"  执行警告: {e}")
            
            logger.info(f"  ✓ 完成: 执行了 {count} 条语句")
        
        conn.commit()
        
        # 验证表
        cursor.execute("SHOW TABLES")
        tables = [r[0] for r in cursor.fetchall()]
        logger.info(f"初始化完成，当前数据库共有 {len(tables)} 个表:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
            
        logger.info("=" * 60)
        logger.info("✓ 快速初始化任务圆满完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 快速初始化失败: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.debug("数据库连接已关闭")


if __name__ == "__main__":
    run_quick_init()
