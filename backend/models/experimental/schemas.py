"""通用请求响应模型"""
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime


class DataQueryParams(BaseModel):
    """通用数据查询参数"""
    page: int = 1
    page_size: int = 20
    filters: Optional[Dict[str, Any]] = None


class DataSearchParams(BaseModel):
    """通用数据搜索参数"""
    keyword: str
    page: int = 1
    page_size: int = 20


class DataResponse(BaseModel):
    """通用数据响应"""
    data: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int


class DataCreateResponse(BaseModel):
    """创建数据响应"""
    message: str
    data_id: int


class DataUpdateResponse(BaseModel):
    """更新数据响应"""
    message: str


class DataDeleteResponse(BaseModel):
    """删除数据响应"""
    message: str


class BatchImportResponse(BaseModel):
    """批量导入响应"""
    message: str
    dataset_id: str
    filename: str
    success: int
    duplicates: int
    failed: int
    total: int
    errors: Optional[List[str]] = None
    # 新增字段（支持自动创建数据集）
    dataset_created: Optional[bool] = None
    table_name: Optional[str] = None
    fields_count: Optional[int] = None
    creation_message: Optional[str] = None


class DatasetSchemaResponse(BaseModel):
    """数据集结构响应"""
    dataset_id: str
    display_name: str
    table_name: str
    fields: List[Dict[str, Any]]
    categories: Dict[str, List[str]]
    searchable_fields: List[str]
    required_fields: List[str]
    total_fields: int


class DatasetListResponse(BaseModel):
    """数据集列表响应"""
    datasets: List[Dict[str, str]]
    total: int
