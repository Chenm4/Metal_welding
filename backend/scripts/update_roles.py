"""更新数据库中的用户角色"""
import sys6


from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pymysql
from backend.config import Settings

settings = Settings()

def update_roles():
    """将 viewer 角色更新为 user"""
    conn = pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset='utf8mb4'
    )
    
    try:
        cursor = conn.cursor()
        
        # 更新 viewer 为 user
        cursor.execute("UPDATE sys_users SET role = 'user' WHERE role = 'viewer'")
        conn.commit()
        
        print(f"✓ 已更新 {cursor.rowcount} 条记录: viewer -> user")
        
        # 显示当前所有用户
        cursor.execute("SELECT id, username, role FROM sys_users")
        users = cursor.fetchall()
        print("\n当前用户列表:")
        for user in users:
            print(f"  ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}")
            
    finally:
        conn.close()

if __name__ == "__main__":
    update_roles()
