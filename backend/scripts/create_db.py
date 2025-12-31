"""
创建数据库脚本

本脚本用于初始化MySQL数据库环境，从配置文件读取数据库名称并创建。
这是整个项目的第一步，必须在其他脚本之前执行。

功能：
1. 连接到MySQL服务器（不指定数据库）
2. 从配置文件读取数据库名称并创建（如果不存在）
3. 设置数据库字符集为utf8mb4（支持完整Unicode）
4. 验证数据库创建成功

使用方式：
    cd backend/scripts
    python create_db.py
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


def create_database():
    """
    从配置文件读取数据库名称并创建
    
    功能说明：
    1. 连接到MySQL服务器（不指定数据库名）
    2. 执行CREATE DATABASE命令创建数据库
    3. 使用IF NOT EXISTS避免重复创建错误
    4. 设置utf8mb4字符集，支持所有Unicode字符（包括emoji）
    5. 验证数据库是否成功创建并可用
    
    数据库配置：
        - 名称: 从 settings.MYSQL_DATABASE 读取
        - 字符集: utf8mb4
        - 排序规则: utf8mb4_unicode_ci
        - 主机: 从 settings.MYSQL_HOST 读取
        - 端口: 从 settings.MYSQL_PORT 读取
    
    Returns:
        bool: 创建成功返回True，失败返回False
    
    Raises:
        Exception: 数据库操作失败时记录错误日志
    
    使用示例：
        if create_database():
            logger.info("数据库创建成功，可以继续执行init_db.py")
        else:
            logger.error("数据库创建失败，请检查MySQL服务和权限")
    """
    connection = None
    try:
        # 连接到MySQL服务器（不指定数据库）
        logger.info("正在连接到MySQL服务器...")
        connection = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        logger.info("✓ 连接到MySQL服务器成功")
        logger.info(f"  主机: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
        logger.info(f"  用户: {settings.MYSQL_USER}")
        
        cursor = connection.cursor()
        
        # 创建数据库（如果不存在）
        logger.info("")
        logger.info("正在创建数据库...")
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS {settings.MYSQL_DATABASE} "
            "DEFAULT CHARACTER SET utf8mb4 "
            "DEFAULT COLLATE utf8mb4_unicode_ci"
        )
        logger.info(f"✓ 数据库 '{settings.MYSQL_DATABASE}' 创建成功")
        logger.info(f"  字符集: utf8mb4")
        logger.info(f"  排序规则: utf8mb4_unicode_ci")
        
        # 验证数据库是否存在
        cursor.execute("SHOW DATABASES")
        databases = [row[0] for row in cursor.fetchall()]
        
        if settings.MYSQL_DATABASE in databases:
            logger.info("")
            logger.info("✓ 数据库验证通过，已存在并可用")
            logger.debug(f"所有数据库: {', '.join(databases)}")
        else:
            logger.error("✗ 数据库验证失败，未在数据库列表中找到")
            return False
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 创建数据库失败: {str(e)}", exc_info=True)
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
    主函数：执行数据库创建流程
    
    功能说明：
    1. 打印程序启动横幅
    2. 调用create_database()创建数据库
    3. 根据结果输出成功或失败信息
    4. 提示下一步操作（运行init_db.py）
    5. 记录完整的执行日志
    
    Returns:
        None
    
    使用方式：
        cd backend/scripts
        python create_db.py
    """
    # 打印启动横幅
    logger.info("=" * 60)
    logger.info("MySQL数据库创建工具")
    logger.info("=" * 60)
    logger.info("")
    
    # 执行数据库创建
    success = create_database()
    
    # 输出结果
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("✓ 完成！现在可以运行 init_db.py 初始化表结构")
        logger.info("")
        logger.info("下一步命令:")
        logger.info("  cd backend/scripts")
        logger.info("  python init_db.py")
    else:
        logger.error("✗ 失败！请检查：")
        logger.error("  1. MySQL服务是否启动")
        logger.error("  2. root用户密码是否正确")
        logger.error("  3. 用户是否有CREATE DATABASE权限")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()

