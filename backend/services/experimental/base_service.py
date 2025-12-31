"""通用实验数据服务 - 零硬编码，元数据驱动"""
import pymysql
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from backend.models.experimental.metadata import DatasetMetadata
from backend.config import Settings


settings = Settings()


class BaseExperimentalDataService:
    """通用实验数据服务 - 支持所有数据集"""
    
    def __init__(self, dataset_id: str):
        """
        初始化服务
        
        Args:
            dataset_id: 数据集ID，如 'batch_1'
        """
        self.dataset_id = dataset_id
        self.metadata = DatasetMetadata(dataset_id)
        self.table_name = self.metadata.get_table_name()
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
    
    def _escape_field_name(self, field_name: str) -> str:
        """转义字段名（处理%等特殊字符）"""
        return field_name.replace('%', '%%')
    
    def _ensure_table_exists(self, cursor):
        """确保数据库表存在，否则抛出异常"""
        cursor.execute(f"SHOW TABLES LIKE '{self.table_name}'")
        if not cursor.fetchone():
            raise ValueError(f"数据集对应的数据库表不存在: {self.table_name}")
    
    # ========== 查询操作 ==========
    
    def list_data(
        self,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Dict], int]:
        """
        分页查询数据（通用）
        
        Args:
            page: 页码
            page_size: 每页数量
            filters: 过滤条件字典
            
        Returns:
            (data_list, total_count)
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 检查表是否存在
            self._ensure_table_exists(cursor)

            # 构建WHERE子句
            where_clauses = []
            params = []
            
            if filters:
                all_fields = set(self.metadata.get_all_field_names())
                for key, value in filters.items():
                    if key in all_fields and value is not None:
                        where_clauses.append(f"`{self._escape_field_name(key)}` = %s")
                        params.append(value)
            
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {self.table_name} WHERE {where_sql}"
            cursor.execute(count_sql, tuple(params))
            total = cursor.fetchone()['total']
            
            # 分页查询数据
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {self.table_name} 
                WHERE {where_sql} 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, tuple(params + [page_size, offset]))
            data_list = cursor.fetchall()
            
            return data_list, total
            
        finally:
            conn.close()
    
    def search(
        self,
        keyword: str,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[Dict], int]:
        """
        关键词搜索（通用）
        
        Args:
            keyword: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            (data_list, total_count)
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 检查表是否存在
            self._ensure_table_exists(cursor)

            # 从元数据获取可搜索字段
            search_fields = self.metadata.get_searchable_fields()
            
            if not search_fields:
                # 如果没有定义可搜索字段，返回空结果
                return [], 0
            
            # 构建搜索条件
            search_clauses = [
                f"`{self._escape_field_name(field)}` LIKE %s" 
                for field in search_fields
            ]
            search_sql = " OR ".join(search_clauses)
            search_params = [f"%{keyword}%"] * len(search_fields)
            
            # 查询总数
            count_sql = f"SELECT COUNT(*) as total FROM {self.table_name} WHERE {search_sql}"
            cursor.execute(count_sql, tuple(search_params))
            total = cursor.fetchone()['total']
            
            # 分页查询
            offset = (page - 1) * page_size
            data_sql = f"""
                SELECT * FROM {self.table_name} 
                WHERE {search_sql} 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
            """
            cursor.execute(data_sql, tuple(search_params + [page_size, offset]))
            data_list = cursor.fetchall()
            
            return data_list, total
            
        finally:
            conn.close()
    
    def get_by_id(self, data_id: int) -> Optional[Dict]:
        """根据ID获取单条数据"""
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            sql = f"SELECT * FROM {self.table_name} WHERE id = %s"
            cursor.execute(sql, (data_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    #========== 创建/更新/删除操作 ==========
    
    def _check_duplicate(self, conn, data: Dict, exclude_id: Optional[int] = None) -> bool:
        """
        检查是否存在完全相同的记录
        
        Args:
            conn: 数据库连接
            data: 数据字典
            exclude_id: 排除的记录ID（用于更新时检查）
            
        Returns:
            是否存在重复
        """
        cursor = conn.cursor()
        
        # 获取需要比较的字段（排除审计字段）
        check_fields = [
            k for k in data.keys() 
            if k not in self.metadata.get_audit_fields() and k != 'id'
        ]
        
        if not check_fields:
            return False
        
        # 构建检查条件
        where_clauses = []
        check_values = []
        
        for key in check_fields:
            value = data[key]
            if value is None or value == '' or str(value).strip() in self.settings.NULL_VALUES:
                # 空值检查
                null_conditions = " OR ".join(["%s"] * len(self.settings.NULL_VALUES))
                where_clauses.append(
                    f"(`{self._escape_field_name(key)}` IS NULL OR "
                    f"`{self._escape_field_name(key)}` = '' OR "
                    f"TRIM(`{self._escape_field_name(key)}`) IN ({null_conditions}))"
                )
                check_values.extend(self.settings.NULL_VALUES)
            else:
                where_clauses.append(f"`{self._escape_field_name(key)}` = %s")
                check_values.append(value)
        
        # 添加排除条件
        if exclude_id:
            where_clauses.append("id != %s")
            check_values.append(exclude_id)
        
        check_sql = f"""
            SELECT COUNT(*) as count FROM {self.table_name} 
            WHERE {' AND '.join(where_clauses)}
        """
        cursor.execute(check_sql, tuple(check_values))
        result = cursor.fetchone()
        
        return result['count'] > 0
    
    def create(self, data: Dict, created_by: str) -> int:
        """
        创建数据
        
        Args:
            data: 数据字典
            created_by: 创建者
            
        Returns:
            新创建记录的ID
            
        Raises:
            ValueError: 数据验证失败或存在重复
        """
        # 验证字段
        valid, error_msg = self.metadata.validate_fields(data)
        if not valid:
            raise ValueError(error_msg)
        
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            
            # 检查重复
            if self._check_duplicate(conn, data):
                raise ValueError("数据已存在，不允许插入完全相同的记录")
            
            cursor = conn.cursor()
            
            # 添加审计字段
            data['created_by'] = created_by
            data['updated_by'] = created_by
            
            # 构建INSERT语句
            columns = list(data.keys())
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join([f'`{self._escape_field_name(col)}`' for col in columns])
            
            sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
            values = tuple(data.values())
            
            cursor.execute(sql, values)
            conn.commit()
            
            return cursor.lastrowid
            
        finally:
            conn.close()
    
    def update(self, data_id: int, data: Dict, updated_by: str) -> bool:
        """
        更新数据
        
        Args:
            data_id: 数据ID
            data: 更新的字段
            updated_by: 更新者
            
        Returns:
            是否更新成功
        """
        if not data:
            raise ValueError("没有提供更新字段")
        
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            
            # 添加审计字段
            data['updated_by'] = updated_by
            
            # 构建UPDATE语句
            set_clauses = [f"`{self._escape_field_name(k)}` = %s" for k in data.keys()]
            set_sql = ', '.join(set_clauses)
            values = list(data.values()) + [data_id]
            
            sql = f"UPDATE {self.table_name} SET {set_sql} WHERE id = %s"
            cursor.execute(sql, tuple(values))
            conn.commit()
            
            return cursor.rowcount > 0
            
        finally:
            conn.close()
    
    def delete(self, data_id: int) -> bool:
        """删除数据"""
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            sql = f"DELETE FROM {self.table_name} WHERE id = %s"
            cursor.execute(sql, (data_id,))
            conn.commit()
            
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def batch_delete(self, data_ids: List[int]) -> int:
        """
        批量删除数据
        
        Returns:
            删除的记录数
        """
        if not data_ids:
            return 0
        
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            placeholders = ','.join(['%s'] * len(data_ids))
            sql = f"DELETE FROM {self.table_name} WHERE id IN ({placeholders})"
            cursor.execute(sql, tuple(data_ids))
            conn.commit()
            
            return cursor.rowcount
            
        finally:
            conn.close()
    
    # ========== 批量导入 ==========
    
    def batch_import(self, data_list: List[Dict], created_by: str) -> Dict:
        """
        批量导入数据（带重复检查）
        
        Returns:
            导入统计信息
        """
        conn = self.get_connection()
        
        success_count = 0
        duplicate_count = 0
        failed_count = 0
        errors = []
        
        try:
            cursor = conn.cursor()
            self._ensure_table_exists(cursor)
            
            for idx, data in enumerate(data_list, start=1):
                try:
                    # 检查重复
                    if self._check_duplicate(conn, data):
                        duplicate_count += 1
                        continue
                    
                    # 添加审计字段
                    data['created_by'] = created_by
                    data['updated_by'] = created_by
                    
                    # 构建INSERT语句
                    columns = list(data.keys())
                    placeholders = ', '.join(['%s'] * len(columns))
                    columns_str = ', '.join([f'`{self._escape_field_name(col)}`' for col in columns])
                    
                    sql = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"
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
                "errors": errors[:10]  # 最多返回10条错误
            }
            
        except Exception as e:
            conn.rollback()
            raise Exception(f"批量导入失败: {str(e)}")
        finally:
            conn.close()
    
    def get_table_columns(self) -> List[str]:
        """获取表的所有列名（从元数据）"""
        return self.metadata.get_all_field_names()
