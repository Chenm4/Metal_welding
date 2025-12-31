"""
默认用户初始化脚本

本脚本用于向数据库的系统用户表（sys_users）中插入初始管理账号和普通账号。
在执行前会清空原有的用户数据，确保环境干净。

功能：
1. 建立数据库连接
2. 清空 sys_users 表中的所有记录
3. 插入预设的管理员（admin）和观察者（viewer）账号
4. 验证插入结果并输出当前用户列表
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


def insert_default_users():
    """
    执行默认用户插入逻辑
    
    功能说明：
    1. 连接到数据库
    2. 使用 DELETE 语句清空 sys_users 表
    3. 执行批量插入语句，设置初始用户名、密码和角色
    4. 提交事务并查询验证
    5. 异常处理：确保在发生错误时记录日志并关闭连接
    """
    logger.info("=" * 60)
    logger.info("开始初始化默认用户信息")
    logger.info("=" * 60)
    
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
        
        # 1. 删除现有用户
        logger.info("正在清空 sys_users 表...")
        cursor.execute('DELETE FROM sys_users')
        logger.debug("  sys_users 表已清空")
        
        # 2. 插入默认用户
        logger.info("正在插入预设用户数据...")
        sql = """
        INSERT INTO sys_users (username, password, role, created_by) 
        VALUES 
            ('admin', '123456', 'admin', 'system'),
            ('viewer', '123456', 'viewer', 'admin')
        """
        cursor.execute(sql)
        conn.commit()
        logger.info("✓ 默认用户插入成功")
        
        # 3. 查询验证
        cursor.execute('SELECT id, username, role, created_at FROM sys_users')
        users = cursor.fetchall()
        logger.info(f"当前系统用户总数: {len(users)}")
        
        for user in users:
            logger.info(f"  - ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}, 创建时间: {user[3]}")
            
        logger.info("=" * 60)
        logger.info("✓ 用户初始化任务完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"✗ 初始化用户失败: {e}", exc_info=True)
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logger.debug("数据库连接已关闭")


if __name__ == "__main__":
    insert_default_users()
