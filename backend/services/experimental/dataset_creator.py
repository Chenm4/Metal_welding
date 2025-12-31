"""动态数据集创建服务 - 自动创建表和元数据配置"""
import json
import os
from typing import List, Dict, Any, Tuple
from pathlib import Path
import pymysql

from backend.config import Settings


class DatasetCreator:
    """动态创建新数据集的服务类"""
    
    def __init__(self):
        self.settings = Settings()
        self.metadata_file = Path(__file__).parent.parent.parent / "config" / "dataset_metadata.json"
    
    def check_dataset_exists(self, dataset_id: str) -> Tuple[bool, bool]:
        """
        检查数据集是否存在
        
        Returns:
            (metadata_exists, table_exists)
        """
        # 检查元数据
        metadata_exists = False
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
                metadata_exists = dataset_id in metadata.get("datasets", {})
        except FileNotFoundError:
            pass
        
        # 检查数据库表
        table_exists = False
        table_name = f"exp_data_{dataset_id}"
        conn = pymysql.connect(
            host=self.settings.MYSQL_HOST,
            port=self.settings.MYSQL_PORT,
            user=self.settings.MYSQL_USER,
            password=self.settings.MYSQL_PASSWORD,
            database=self.settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        try:
            cursor = conn.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            table_exists = cursor.fetchone() is not None
        finally:
            conn.close()
        
        return metadata_exists, table_exists
    
    def infer_field_info(self, column_name: str) -> Dict[str, Any]:
        """
        根据字段名推断字段信息
        
        分类规则：
        - 物性_xxx → category: "物性"
        - 工艺_xxx → category: "工艺"
        - 状态_xxx → category: "状态"
        - 性能_xxx → category: "性能"
        """
        field_info = {
            "name": column_name,
            "type": "string",  # 默认字符串类型，MySQL会自动转换
            "nullable": True
        }
        
        # 推断分类
        if column_name.startswith("物性_"):
            field_info["category"] = "物性"
        elif column_name.startswith("工艺_"):
            field_info["category"] = "工艺"
        elif column_name.startswith("状态_"):
            field_info["category"] = "状态"
        elif column_name.startswith("性能_"):
            field_info["category"] = "性能"
        
        return field_info
    
    def generate_table_name(self, dataset_id: str) -> str:
        """生成表名"""
        return f"exp_data_{dataset_id}"
    
    def create_database_table(self, dataset_id: str, columns: List[str]) -> str:
        """
        创建数据库表
        
        Args:
            dataset_id: 数据集ID
            columns: CSV列名列表
            
        Returns:
            创建的表名
        """
        table_name = self.generate_table_name(dataset_id)
        
        conn = pymysql.connect(
            host=self.settings.MYSQL_HOST,
            port=self.settings.MYSQL_PORT,
            user=self.settings.MYSQL_USER,
            password=self.settings.MYSQL_PASSWORD,
            database=self.settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        
        try:
            cursor = conn.cursor()
            
            # 构建CREATE TABLE语句
            # 标准字段
            sql_parts = [
                f"CREATE TABLE IF NOT EXISTS `{table_name}` (",
                "  `id` INT AUTO_INCREMENT PRIMARY KEY,",
            ]
            
            # 数据字段（所有CSV列都设为TEXT类型，可存储任意长度）
            for col in columns:
                escaped_col = col.replace("`", "``")  # 转义反引号
                sql_parts.append(f"  `{escaped_col}` TEXT DEFAULT NULL,")
            
            # 审计字段
            sql_parts.extend([
                "  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,",
                "  `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,",
                "  `created_by` VARCHAR(50) DEFAULT NULL,",
                "  `updated_by` VARCHAR(50) DEFAULT NULL",
                ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
            ])
            
            sql = "\n".join(sql_parts)
            cursor.execute(sql)
            conn.commit()
            
            return table_name
            
        finally:
            conn.close()
    
    def generate_metadata_config(self, dataset_id: str, columns: List[str]) -> Dict[str, Any]:
        """
        生成元数据配置
        
        Args:
            dataset_id: 数据集ID
            columns: CSV列名列表
            
        Returns:
            数据集元数据配置字典
        """
        table_name = self.generate_table_name(dataset_id)
        
        # 提取批次号（如果有）
        batch_num = dataset_id.replace("batch_", "") if dataset_id.startswith("batch_") else dataset_id
        
        # 生成字段信息
        data_fields = [self.infer_field_info(col) for col in columns]
        
        # 注意：不再生成 searchable_fields 配置
        # 所有 data_fields 默认都可搜索，由代码动态获取
        
        # 必填字段：编号字段（如果存在）
        required_fields = []
        if "编号" in columns:
            required_fields.append("编号")
        
        # 审计字段
        audit_fields = ["created_at", "updated_at", "created_by", "updated_by"]
        
        config = {
            "table_name": table_name,
            "display_name": f"第{batch_num}批实验数据" if batch_num.isdigit() else f"{dataset_id}实验数据",
            "description": f"{'批次' if batch_num.isdigit() else ''}{batch_num}的激光焊接实验数据",
            "fields": {
                "data_fields": data_fields,
                "required_fields": required_fields,
                "audit_fields": audit_fields
            },
            "coverage": {
                "threshold": 0.9,
                "exclude_from_calculation": [
                    "id", "created_at", "updated_at", "created_by", "updated_by",
                    "deleted_at", "is_deleted", "version"
                ]
            }
        }
        
        return config
    
    def save_metadata_config(self, dataset_id: str, config: Dict[str, Any]) -> None:
        """
        保存元数据配置到JSON文件
        
        Args:
            dataset_id: 数据集ID
            config: 配置字典
        """
        # 确保配置目录存在
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有配置
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {"datasets": {}}
        
        # 添加新配置
        if "datasets" not in metadata:
            metadata["datasets"] = {}
        
        metadata["datasets"][dataset_id] = config
        
        # 保存
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def create_new_dataset(self, dataset_id: str, csv_columns: List[str]) -> Dict[str, Any]:
        """
        创建新数据集（表 + 元数据配置）
        
        Args:
            dataset_id: 数据集ID
            csv_columns: CSV文件的列名列表
            
        Returns:
            创建结果信息
        """
        # 检查是否已存在
        metadata_exists, table_exists = self.check_dataset_exists(dataset_id)
        
        if metadata_exists and table_exists:
            return {
                "created": False,
                "message": "数据集已存在",
                "dataset_id": dataset_id,
                "table_name": self.generate_table_name(dataset_id)
            }
        
        # 创建数据库表
        if not table_exists:
            table_name = self.create_database_table(dataset_id, csv_columns)
        else:
            table_name = self.generate_table_name(dataset_id)
        
        # 生成并保存元数据配置
        if not metadata_exists:
            config = self.generate_metadata_config(dataset_id, csv_columns)
            self.save_metadata_config(dataset_id, config)
        
        return {
            "created": True,
            "message": "数据集创建成功",
            "dataset_id": dataset_id,
            "table_name": table_name,
            "fields_count": len(csv_columns),
            "table_created": not table_exists,
            "metadata_created": not metadata_exists
        }
