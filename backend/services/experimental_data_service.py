"""实验数据业务逻辑"""
import pymysql
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from backend.config import Settings


settings = Settings()


class ExperimentalDataService:
    """实验数据服务层"""
    
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
    
    def get_table_name(self, batch_id: int) -> str:
        """获取批次表名"""
        if batch_id < 1 or batch_id > 4:
            raise ValueError(f"批次ID必须在1-4之间，当前: {batch_id}")
        return f"exp_data_batch_{batch_id}"
    
    def list_data(
        self,
        batch_id: int,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict] = None
    ) -> Tuple[List[Dict], int]:
        """
        分页查询实验数据
        
        Returns:
            (data_list, total_count)
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 构建WHERE子句
            where_clauses = []
            params = []
            
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        where_clauses.append(f"`{key}` = %s")
                        params.append(value)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {where_sql}"
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()['total']
            
            # 分页查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {table_name} 
                WHERE {where_sql} 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, tuple(params + [page_size, offset]))
            data_list = cursor.fetchall()
            
            return data_list, total
            
        finally:
            conn.close()
    
    def get_by_id(self, batch_id: int, data_id: int) -> Optional[Dict]:
        """根据ID获取单条数据"""
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = f"SELECT * FROM {table_name} WHERE id = %s"
            cursor.execute(sql, (data_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def create(self, batch_id: int, data: Dict, created_by: str) -> int:
        """
        创建实验数据
        
        Returns:
            新创建记录的ID
        
        Raises:
            ValueError: 如果数据已存在（完全重复）
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 检查是否存在完全相同的记录（排除id和自动生成的字段）
            check_data = {k: v for k, v in data.items() if k not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']}
            
            if check_data:
                # 构建检查条件
                where_clauses = []
                check_values = []
                
                for key, value in check_data.items():
                    if value is None or value == '' or str(value).strip() in self.settings.NULL_VALUES:
                        # 空值检查
                        where_clauses.append(f"(`{key.replace('%', '%%')}` IS NULL OR `{key.replace('%', '%%')}` = '' OR TRIM(`{key.replace('%', '%%')}`) IN ({','.join(['%s'] * len(self.settings.NULL_VALUES))}))")
                        check_values.extend(self.settings.NULL_VALUES)
                    else:
                        # 非空值检查
                        where_clauses.append(f"`{key.replace('%', '%%')}` = %s")
                        check_values.append(value)
                
                check_sql = f"SELECT COUNT(*) as count FROM {table_name} WHERE {' AND '.join(where_clauses)}"
                cursor.execute(check_sql, tuple(check_values))
                result = cursor.fetchone()
                
                if result['count'] > 0:
                    raise ValueError("数据已存在，不允许插入完全相同的记录")
            
            # 添加审计字段
            data['created_by'] = created_by
            data['updated_by'] = created_by
            
            # 构建INSERT语句
            columns = [k for k in data.keys()]
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'`{col.replace("%", "%%")}`' for col in columns])
            
            sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            values = tuple(data.values())
            
            cursor.execute(sql, values)
            conn.commit()
            
            return cursor.lastrowid
            
        finally:
            conn.close()
    
    def update(self, batch_id: int, data_id: int, data: Dict, updated_by: str) -> bool:
        """
        更新实验数据
        
        Returns:
            是否更新成功
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 添加审计字段
            data['updated_by'] = updated_by
            
            # 构建UPDATE语句
            set_clauses = [f"`{k.replace('%', '%%')}` = %s" for k in data.keys()]
            set_sql = ', '.join(set_clauses)
            values = list(data.values()) + [data_id]
            
            sql = f"UPDATE {table_name} SET {set_sql} WHERE id = %s"
            cursor.execute(sql, tuple(values))
            conn.commit()
            
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def delete(self, batch_id: int, data_id: int) -> bool:
        """
        删除实验数据
        
        Returns:
            是否删除成功
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = f"DELETE FROM {table_name} WHERE id = %s"
            cursor.execute(sql, (data_id,))
            conn.commit()
            
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def batch_delete(self, batch_id: int, data_ids: List[int]) -> int:
        """
        批量删除实验数据
        
        Returns:
            删除的记录数
        """
        if not data_ids:
            return 0
        
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            placeholders = ','.join(['%s'] * len(data_ids))
            sql = f"DELETE FROM {table_name} WHERE id IN ({placeholders})"
            cursor.execute(sql, tuple(data_ids))
            conn.commit()
            
            return cursor.rowcount
            
        finally:
            conn.close()
    
    def search(
        self,
        batch_id: int,
        keyword: str,
        search_fields: List[str],
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        关键词搜索
        
        Args:
            batch_id: 批次ID
            keyword: 搜索关键词
            search_fields: 搜索字段列表
            page: 页码
            page_size: 每页数量
            
        Returns:
            (data_list, total_count)
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 构建搜索条件
            search_clauses = [f"`{field}` LIKE %s" for field in search_fields]
            search_sql = " OR ".join(search_clauses)
            search_params = [f"%{keyword}%"] * len(search_fields)
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {table_name} WHERE {search_sql}"
            cursor.execute(count_sql, tuple(search_params))
            total = cursor.fetchone()['total']
            
            # 分页查询
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {table_name} 
                WHERE {search_sql} 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, tuple(search_params + [page_size, offset]))
            data_list = cursor.fetchall()
            
            return data_list, total
            
        finally:
            conn.close()
    
    def table_exists(self, batch_id: int) -> bool:
        """
        检查指定批次的表是否存在
        
        Args:
            batch_id: 批次ID
            
        Returns:
            bool: 表存在返回True，否则返回False
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = f"SHOW TABLES LIKE '{table_name}'"
            cursor.execute(sql)
            result = cursor.fetchone()
            return result is not None
        finally:
            conn.close()
    
    def create_table_from_columns(self, batch_id: int, columns: List[str]) -> str:
        """
        根据列名列表创建数据库表
        
        Args:
            batch_id: 批次ID
            columns: 列名列表
            
        Returns:
            str: 创建的表名
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 构建CREATE TABLE语句
            sql_parts = [
                f"CREATE TABLE IF NOT EXISTS `{table_name}` (",
                "  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '记录ID',",
            ]
            
            # 数据字段（所有CSV列都设为TEXT类型）
            for col in columns:
                escaped_col = col.replace("`", "``")  # 转义反引号
                sql_parts.append(f"  `{escaped_col}` TEXT DEFAULT NULL COMMENT '{escaped_col}',")
            
            # 审计字段
            sql_parts.extend([
                "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',",
                "  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',",
                "  `created_by` VARCHAR(50) DEFAULT NULL COMMENT '创建人',",
                "  `updated_by` VARCHAR(50) DEFAULT NULL COMMENT '更新人'",
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
            ])
            
            sql = "\n".join(sql_parts)
            cursor.execute(sql)
            conn.commit()
            
            return table_name
            
        finally:
            conn.close()
    
    def get_table_columns(self, batch_id: int) -> List[str]:
        """
        获取指定批次表的列名（排除自动生成的字段）
        
        Args:
            batch_id: 批次ID
            
        Returns:
            列名列表
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            sql = f"SHOW COLUMNS FROM {table_name}"
            cursor.execute(sql)
            columns = cursor.fetchall()
            
            # 排除自动生成的字段
            excluded_fields = {'id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'is_deleted', 'version'}
            column_names = [col['Field'] for col in columns if col['Field'] not in excluded_fields]
            
            return column_names
            
        finally:
            conn.close()
    
    def batch_import(self, batch_id: int, data_list: List[Dict], created_by: str) -> Dict:
        """
        批量导入数据（带重复检查）
        
        Args:
            batch_id: 批次ID
            data_list: 数据列表
            created_by: 创建者
            
        Returns:
            {
                "success": 成功插入数量,
                "duplicates": 重复跳过数量,
                "failed": 失败数量,
                "errors": 错误信息列表
            }
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        success_count = 0
        duplicate_count = 0
        failed_count = 0
        errors = []
        
        try:
            cursor = conn.cursor()
            
            for idx, data in enumerate(data_list, start=1):
                try:
                    # 检查是否存在完全相同的记录
                    check_data = {k: v for k, v in data.items() if k not in ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']}
                    
                    if check_data:
                        where_clauses = []
                        check_values = []
                        
                        for key, value in check_data.items():
                            if value is None or value == '' or str(value).strip() in self.settings.NULL_VALUES:
                                where_clauses.append(f"(`{key.replace('%', '%%')}` IS NULL OR `{key.replace('%', '%%')}` = '' OR TRIM(`{key.replace('%', '%%')}`) IN ({','.join(['%s'] * len(self.settings.NULL_VALUES))}))")
                                check_values.extend(self.settings.NULL_VALUES)
                            else:
                                where_clauses.append(f"`{key.replace('%', '%%')}` = %s")
                                check_values.append(value)
                        
                        check_sql = f"SELECT COUNT(*) as count FROM {table_name} WHERE {' AND '.join(where_clauses)}"
                        cursor.execute(check_sql, tuple(check_values))
                        result = cursor.fetchone()
                        
                        if result['count'] > 0:
                            duplicate_count += 1
                            continue
                    
                    # 添加审计字段
                    data['created_by'] = created_by
                    data['updated_by'] = created_by
                    
                    # 构建INSERT语句
                    columns = [k for k in data.keys()]
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join([f'`{col.replace("%", "%%")}`' for col in columns])
                    
                    sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    values = tuple(data.values())
                    
                    cursor.execute(sql, values)
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"第{idx}行: {str(e)}")
            
            conn.commit()
            
            return {
                "success": success_count,
                "duplicates": duplicate_count,
                "failed": failed_count,
                "total": len(data_list),
                "errors": errors[:10]  # 最多返回10条错误信息
            }
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"批量导入失败: {str(e)}")
        finally:
            conn.close()
