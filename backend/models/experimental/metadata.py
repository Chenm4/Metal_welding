"""数据集元数据管理器"""
import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from functools import lru_cache


class DatasetMetadata:
    """数据集元数据管理器 - 零硬编码，完全配置驱动"""
    
    _config_cache = None
    
    def __init__(self, dataset_id: str):
        """
        初始化元数据管理器
        
        Args:
            dataset_id: 数据集ID，如 '1', '2'
        """
        self.dataset_id = dataset_id
        self.config = self._load_dataset_config(dataset_id)
    
    @classmethod
    def _load_all_metadata(cls) -> dict:
        """加载所有元数据配置（带缓存）"""
        if cls._config_cache is None:
            config_path = Path(__file__).parent.parent.parent / 'config' / 'dataset_metadata.json'
            
            if not config_path.exists():
                raise FileNotFoundError(f"元数据配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                cls._config_cache = json.load(f)
        
        return cls._config_cache
    
    @classmethod
    def reload_metadata(cls):
        """强制重新加载元数据（用于新数据集创建后）"""
        cls._config_cache = None
    
    def _load_dataset_config(self, dataset_id: str) -> dict:
        """加载指定数据集的配置"""
        all_metadata = self._load_all_metadata()
        
        if dataset_id not in all_metadata['datasets']:
            available = ', '.join(all_metadata['datasets'].keys())
            raise ValueError(f"数据集 '{dataset_id}' 不存在。可用的数据集: {available}")
        
        return all_metadata['datasets'][dataset_id]
    
    @classmethod
    def list_all_datasets(cls) -> List[Dict[str, str]]:
        """列出所有可用的数据集"""
        all_metadata = cls._load_all_metadata()
        
        return [
            {
                "id": dataset_id,
                "display_name": config["display_name"],
                "table_name": config["table_name"],
                "description": config["description"]
            }
            for dataset_id, config in all_metadata['datasets'].items()
        ]
    
    @classmethod
    def validate_dataset_id(cls, dataset_id: str) -> bool:
        """验证数据集ID是否存在"""
        all_metadata = cls._load_all_metadata()
        return dataset_id in all_metadata['datasets']
    
    # ========== 表信息 ==========
    
    def get_table_name(self) -> str:
        """获取表名"""
        return self.config['table_name']
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return self.config['display_name']
    
    def get_description(self) -> str:
        """获取描述"""
        return self.config.get('description', '')
    
    # ========== 字段信息 ==========
    
    def get_all_field_names(self) -> List[str]:
        """获取所有数据字段名（不包括审计字段）"""
        return [field['name'] for field in self.config['fields']['data_fields']]
    
    def get_data_fields(self) -> List[Dict]:
        """获取所有数据字段详细信息"""
        return self.config['fields']['data_fields']
    
    def get_fields_by_category(self, category: str) -> List[str]:
        """
        按分类获取字段
        
        Args:
            category: 分类名称，如 '物性', '工艺', '状态', '性能'
        """
        return [
            field['name'] 
            for field in self.config['fields']['data_fields']
            if field.get('category') == category
        ]
    
    def get_all_categories(self) -> Dict[str, List[str]]:
        """获取所有分类及其字段"""
        categories = {}
        for field in self.config['fields']['data_fields']:
            category = field.get('category')
            if category:
                if category not in categories:
                    categories[category] = []
                categories[category].append(field['name'])
        return categories
    
    def get_searchable_fields(self) -> List[str]:
        """获取可搜索字段
        
        返回所有数据字段（data_fields）的字段名，不包括审计字段。
        这样所有数据都可以被搜索，提供更好的搜索体验。
        
        Returns:
            所有可搜索的字段名列表（排除审计字段）
        """
        # 直接返回所有data_fields的字段名
        # 不再依赖JSON中的searchable_fields配置
        return self.get_all_field_names()
    
    def get_required_fields(self) -> List[str]:
        """获取必填字段"""
        return self.config['fields'].get('required_fields', [])
    
    def get_audit_fields(self) -> List[str]:
        """获取审计字段"""
        return self.config['fields'].get('audit_fields', [])
    
    # ========== 覆盖率配置 ==========
    
    def get_coverage_threshold(self) -> float:
        """获取覆盖率阈值"""
        return self.config['coverage']['threshold']
    
    def get_coverage_exclude_fields(self) -> List[str]:
        """获取覆盖率计算时需要排除的字段"""
        return self.config['coverage']['exclude_from_calculation']
    
    def get_coverage_calculation_fields(self) -> List[str]:
        """获取覆盖率计算时需要包含的字段（排除审计字段后）"""
        all_fields = self.get_all_field_names()
        exclude_fields = set(self.get_coverage_exclude_fields())
        return [f for f in all_fields if f not in exclude_fields]
    
    # ========== 验证方法 ==========
    
    def validate_fields(self, data: dict) -> Tuple[bool, Optional[str]]:
        """
        验证数据字段是否符合元数据定义
        
        Args:
            data: 待验证的数据字典
            
        Returns:
            (是否有效, 错误信息)
        """
        all_fields = set(self.get_all_field_names())
        data_fields = set(data.keys()) - set(self.get_audit_fields())
        
        # 检查多余字段
        extra_fields = data_fields - all_fields
        if extra_fields:
            return False, f"包含未定义的字段: {', '.join(extra_fields)}"
        
        # 检查必填字段
        required_fields = set(self.get_required_fields())
        missing_fields = required_fields - set(data.keys())
        if missing_fields:
            return False, f"缺少必填字段: {', '.join(missing_fields)}"
        
        return True, None
    
    def validate_import_columns(self, file_columns: List[str]) -> Tuple[bool, Optional[str]]:
        """
        验证导入文件的列名是否匹配
        
        Args:
            file_columns: 文件中的列名列表
            
        Returns:
            (是否有效, 错误信息)
        """
        expected_columns = set(self.get_all_field_names())
        file_columns_set = set(file_columns)
        
        missing = expected_columns - file_columns_set
        extra = file_columns_set - expected_columns
        
        if missing or extra:
            msg = "文件列名与数据库表结构不一致！\n"
            if missing:
                msg += f"缺少的列: {', '.join(sorted(missing))}\n"
            if extra:
                msg += f"多余的列: {', '.join(sorted(extra))}\n"
            msg += f"\n数据库需要的列名 ({len(expected_columns)}个):\n"
            msg += ', '.join(sorted(expected_columns))
            return False, msg
        
        return True, None
    
    # ========== 工具方法 ==========
    
    def get_field_info(self, field_name: str) -> Optional[Dict]:
        """获取指定字段的详细信息"""
        for field in self.config['fields']['data_fields']:
            if field['name'] == field_name:
                return field
        return None
    
    def is_nullable(self, field_name: str) -> bool:
        """判断字段是否可为空"""
        field_info = self.get_field_info(field_name)
        return field_info.get('nullable', True) if field_info else True
    
    def get_field_type(self, field_name: str) -> Optional[str]:
        """获取字段类型"""
        field_info = self.get_field_info(field_name)
        return field_info.get('type') if field_info else None
    
    def __repr__(self) -> str:
        return f"<DatasetMetadata: {self.dataset_id} ({self.get_display_name()})>"
