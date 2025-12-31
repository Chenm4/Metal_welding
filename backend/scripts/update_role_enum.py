"""
更新数据库表结构和数据：
1. 修改 role 字段的 ENUM 类型
2. 更新现有 viewer 数据为 user
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import pymysql
from backend.config import Settings

settings = Settings()

def update_role_enum():
    """更新角色枚举和数据"""
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
        
        print("Step 1: 查看当前表结构...")
        cursor.execute("SHOW COLUMNS FROM sys_users LIKE 'role'")
        role_column = cursor.fetchone()
        print(f"  当前 role 字段: {role_column}")
        
        print("\nStep 2: 修改 role 字段类型...")
        # 修改 ENUM 类型，添加新的角色
        alter_sql = """
            ALTER TABLE sys_users 
            MODIFY COLUMN role ENUM('root', 'admin', 'user', 'viewer') NOT NULL DEFAULT 'user'
        """
        cursor.execute(alter_sql)
        print("  ✓ 已添加新角色类型")
        
        print("\nStep 3: 更新现有数据...")
        # 更新 viewer 为 user
        cursor.execute("UPDATE sys_users SET role = 'user' WHERE role = 'viewer'")
        updated_count = cursor.rowcount
        print(f"  ✓ 已更新 {updated_count} 条记录: viewer -> user")
        
        print("\nStep 4: 移除旧的 viewer 选项...")
        # 现在可以安全地移除 viewer
        alter_sql2 = """
            ALTER TABLE sys_users 
            MODIFY COLUMN role ENUM('root', 'admin', 'user') NOT NULL DEFAULT 'user'
        """
        cursor.execute(alter_sql2)
        print("  ✓ 已移除 viewer 角色类型")
        
        conn.commit()
        
        print("\nStep 5: 验证结果...")
        cursor.execute("SHOW COLUMNS FROM sys_users LIKE 'role'")
        role_column = cursor.fetchone()
        print(f"  新的 role 字段: {role_column}")
        
        # 显示所有用户
        cursor.execute("SELECT id, username, role FROM sys_users")
        users = cursor.fetchall()
        print(f"\n当前用户列表 (共 {len(users)} 个):")
        for user in users:
            print(f"  ID: {user[0]}, 用户名: {user[1]}, 角色: {user[2]}")
            
        print("\n✓ 角色系统更新完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ 更新失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_role_enum()
