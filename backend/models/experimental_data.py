"""实验数据模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DataSource(str, Enum):
    """数据来源"""
    EXPERIMENT = "experiment"
    LITERATURE = "literature"


class ExperimentalDataBase(BaseModel):
    """实验数据基础模型"""
    编号: Optional[str] = None
    物性_材料: Optional[str] = None
    物性_材料厚度: Optional[str] = None
    接头类型: Optional[str] = None
    光斑尺寸mm: Optional[str] = Field(None, alias="光斑尺寸（mm）")
    视觉系统: Optional[str] = None
    电流: Optional[str] = None
    正面保护气类型: Optional[str] = None
    正面保护气流量Lmin: Optional[str] = Field(None, alias="正面保护气流量（L/min）")
    背面保护气类型: Optional[str] = None
    背面保护气流量Lmin: Optional[str] = Field(None, alias="背面保护气流量（L/min）")
    工艺_激光功率: Optional[str] = None
    工艺_焊接速度: Optional[str] = None
    激光倾角: Optional[str] = None
    离焦量: Optional[str] = None
    送丝速度: Optional[str] = None
    焊丝: Optional[str] = None
    焊丝直径: Optional[str] = None
    焊缝宽度: Optional[str] = None
    熔深mm: Optional[str] = Field(None, alias="熔深（mm）")
    焊脚高度: Optional[str] = None
    焊缝形貌: Optional[str] = None
    内部质量: Optional[str] = None
    尺寸: Optional[str] = None
    性能_拉伸性能温度23C抗拉强度MPa: Optional[str] = Field(None, alias="性能_拉伸性能（温度23℃）抗拉强度MPa")
    性能_拉伸性能温度23C断后伸长率percent: Optional[str] = Field(None, alias="性能_拉伸性能（温度23℃）断后伸长率%")
    性能_拉伸性能温度23C屈服强度MPa: Optional[str] = Field(None, alias="性能_拉伸性能（温度23℃）屈服强度MPa")
    无损照片号: Optional[str] = None
    无损结果: Optional[str] = None
    性能_弯曲性能: Optional[str] = None
    性能_剪切性能: Optional[str] = None
    金相组织: Optional[str] = None
    工艺: Optional[str] = None
    挂靠项目任务号: Optional[str] = None
    
    class Config:
        populate_by_name = True # 这样就能用名字来查找数据中的列名
        from_attributes = True


class ExperimentalDataCreate(ExperimentalDataBase):
    """创建实验数据请求模型"""
    data_source: DataSource = DataSource.EXPERIMENT
    notes: Optional[str] = None


class ExperimentalDataUpdate(BaseModel):
    """更新实验数据请求模型"""
    编号: Optional[str] = None
    物性_材料: Optional[str] = None
    物性_材料厚度: Optional[str] = None
    接头类型: Optional[str] = None
    # ...其他字段可选
    data_source: Optional[DataSource] = None
    notes: Optional[str] = None


class ExperimentalDataResponse(ExperimentalDataBase):
    """实验数据响应模型"""
    id: int
    data_source: DataSource
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class ExperimentalDataQuery(BaseModel):
    """实验数据查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    batch_id: Optional[int] = Field(None, description="批次ID (1-4)")
    编号: Optional[str] = None
    物性_材料: Optional[str] = None
    工艺: Optional[str] = None
    data_source: Optional[DataSource] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
