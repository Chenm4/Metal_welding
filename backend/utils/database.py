"""
数据库连接工具模块
提供MySQL和MongoDB的连接管理
"""

from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pymongo import MongoClient
from typing import Generator
import sys
import os

# 添加父目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# MySQL连接URL
MYSQL_URL = (
    f"mysql+pymysql://{settings.MYSQL_USER}:{settings.MYSQL_PASSWORD}"
    f"@{settings.MYSQL_HOST}:{settings.MYSQL_PORT}/{settings.MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

# 创建数据库引擎
engine = create_engine(
    MYSQL_URL,
    pool_size=settings.MYSQL_POOL_SIZE,
    max_overflow=settings.MYSQL_MAX_OVERFLOW,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG
)

# 创建Session工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()

# MongoDB连接
try:
    mongo_client = MongoClient(
        host=settings.MONGODB_HOST,
        port=settings.MONGODB_PORT,
        serverSelectionTimeoutMS=5000
    )
    mongo_db = mongo_client[settings.MONGODB_DATABASE]
    # 测试连接
    mongo_client.server_info()
    print("MongoDB连接成功")
except Exception as e:
    print(f"MongoDB连接失败: {e}")
    mongo_db = None


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    
    Yields:
        Session: 数据库会话
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_mongo_db():
    """
    获取MongoDB数据库实例
    
    Returns:
        Database: MongoDB数据库
    """
    return mongo_db


def test_mysql_connection() -> bool:
    """
    测试MySQL连接是否正常
    
    Returns:
        bool: 连接成功返回True，否则返回False
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return result.fetchone()[0] == 1
    except Exception as e:
        print(f"MySQL连接测试失败: {e}")
        return False


def execute_sql_file(sql_file_path: str) -> bool:
    """
    执行SQL文件
    
    Args:
        sql_file_path: SQL文件路径
        
    Returns:
        bool: 执行成功返回True，否则返回False
    """
    try:
        with open(sql_file_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割）
        sql_statements = [stmt.strip() for stmt in sql_content.split(';') if stmt.strip()]
        
        with engine.begin() as conn:
            for statement in sql_statements:
                if statement:
                    conn.execute(text(statement))
        
        print(f"SQL文件执行成功: {sql_file_path}")
        return True
    except Exception as e:
        print(f"SQL文件执行失败: {e}")
        return False


def get_table_columns(table_name: str) -> list:
    """
    获取表的所有列名
    
    Args:
        table_name: 表名
        
    Returns:
        list: 列名列表
    """
    try:
        query = text(f"SHOW COLUMNS FROM {table_name}")
        with engine.connect() as conn:
            result = conn.execute(query)
            columns = [row[0] for row in result]
        return columns
    except Exception as e:
        print(f"获取表列失败: {e}")
        return []


def table_exists(table_name: str) -> bool:
    """
    检查表是否存在
    
    Args:
        table_name: 表名
        
    Returns:
        bool: 表存在返回True，否则返回False
    """
    try:
        query = text(f"SHOW TABLES LIKE '{table_name}'")
        with engine.connect() as conn:
            result = conn.execute(query)
            return result.fetchone() is not None
    except Exception as e:
        print(f"检查表存在性失败: {e}")
        return False


if __name__ == "__main__":
    # 测试连接
    print("测试MySQL连接...")
    if test_mysql_connection():
        print("✓ MySQL连接正常")
    else:
        print("✗ MySQL连接失败")
    
    # 测试MongoDB
    if mongo_db is not None:
        print("✓ MongoDB连接正常")
    else:
        print("✗ MongoDB连接失败")
