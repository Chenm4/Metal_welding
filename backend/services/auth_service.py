"""认证服务"""
import pymysql
from typing import Optional, Dict
from datetime import datetime, timedelta
import jwt
from backend.config import Settings


settings = Settings()


class AuthService:
    """认证服务层"""
    
    def __init__(self):
        self.settings = settings
    
    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(
            host=self.settings.MYSQL_HOST,
            port=self.settings.MYSQL_PORT,
            user=self.settings.MYSQL_USER,
            password=self.settings.MYSQL_PASSWORD,
            database=self.settings.MYSQL_DATABASE,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
    
    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """
        用户认证
        
        Returns:
            用户信息（认证成功）或 None（认证失败）
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = """
                SELECT id, username, password, role, status, created_at, last_login
                FROM sys_users 
                WHERE username = %s AND status = 'active'
            """
            cursor.execute(sql, (username,))
            user = cursor.fetchone()
            
            if not user:
                return None
            
            # 简单的明文密码比对（生产环境应使用bcrypt等加密）
            if user['password'] != password:
                return None
            
            # 更新最后登录时间
            update_sql = "UPDATE sys_users SET last_login = %s WHERE id = %s"
            cursor.execute(update_sql, (datetime.now(), user['id']))
            conn.commit()
            
            # 移除密码字段
            del user['password']
            return user
            
        finally:
            conn.close()
    
    def create_access_token(self, user_data: Dict) -> str:
        """
        创建访问令牌
        
        Args:
            user_data: 用户信息
            
        Returns:
            JWT token
        """
        expire = datetime.utcnow() + timedelta(hours=self.settings.JWT_EXPIRE_HOURS)
        
        payload = {
            "sub": user_data['username'],
            "user_id": user_data['id'],
            "role": user_data['role'],
            "exp": expire
        }
        
        token = jwt.encode(
            payload,
            self.settings.JWT_SECRET_KEY,
            algorithm=self.settings.JWT_ALGORITHM
        )
        
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证令牌
        
        Returns:
            令牌载荷或None
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.JWT_SECRET_KEY,
                algorithms=[self.settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.PyJWTError:
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """根据用户名获取用户"""
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = """
                SELECT id, username, role, status, created_at, last_login
                FROM sys_users 
                WHERE username = %s
            """
            cursor.execute(sql, (username,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """根据用户ID获取用户"""
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = """
                SELECT id, username, role, status, created_at, last_login
                FROM sys_users 
                WHERE id = %s
            """
            cursor.execute(sql, (user_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create_user(self, username: str, password: str, role: str, created_by: str) -> int:
        """
        创建用户
        
        Returns:
            新用户ID
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = """
                INSERT INTO sys_users (username, password, role, created_by)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (username, password, role, created_by))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def update_user(self, user_id: int, **updates) -> bool:
        """更新用户信息"""
        if not updates:
            return False
        
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            set_clauses = [f"{k} = %s" for k in updates.keys()]
            set_sql = ', '.join(set_clauses)
            values = list(updates.values()) + [user_id]
            
            sql = f"UPDATE sys_users SET {set_sql} WHERE id = %s"
            cursor.execute(sql, tuple(values))
            conn.commit()
            
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = "DELETE FROM sys_users WHERE id = %s"
            cursor.execute(sql, (user_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def list_users(self, page: int = 1, page_size: int = 20) -> tuple:
        """
        获取用户列表
        
        Returns:
            (users, total_count)
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 查询总数
            cursor.execute("SELECT COUNT(*) as total FROM sys_users")
            total = cursor.fetchone()['total']
            
            # 分页查询
            offset = (page - 1) * page_size
            sql = """
                SELECT id, username, role, status, created_at, last_login, created_by
                FROM sys_users 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (page_size, offset))
            users = cursor.fetchall()
            
            return users, total
        finally:
            conn.close()
