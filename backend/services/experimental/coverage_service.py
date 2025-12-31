"""覆盖率计算服务 - 基于元数据，零硬编码"""
import pymysql
from typing import Dict, List
from backend.models.experimental.metadata import DatasetMetadata
from backend.config import Settings


settings = Settings()


class CoverageService:
    """覆盖率计算服务 - 完全元数据驱动"""
    
    def __init__(self, dataset_id: str):
        """
        初始化服务
        
        Args:
            dataset_id: 数据集ID
        """
        self.dataset_id = dataset_id
        self.metadata = DatasetMetadata(dataset_id)
        self.table_name = self.metadata.get_table_name()
        self.settings = settings
        
        # 从元数据获取需要计算覆盖率的字段
        self.data_fields = self.metadata.get_coverage_calculation_fields()
        self.threshold = self.metadata.get_coverage_threshold()
    
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
    
    def is_empty_value(self, value) -> bool:
        """判断值是否为空"""
        if value is None:
            return True
        if isinstance(value, str):
            value_stripped = value.strip()
            if value_stripped == '' or value_stripped in self.settings.NULL_VALUES:
                return True
        return False
    
    def calculate_row_coverage(self, row: Dict) -> float:
        """
        计算单条记录的数据覆盖率
        
        公式: 数据覆盖率 = 非空的数据项数量 / 数据项总数
        """
        if not row:
            return 0.0
        
        total_fields = 0
        non_empty_fields = 0
        
        for field in self.data_fields:
            if field in row:
                total_fields += 1
                if not self.is_empty_value(row[field]):
                    non_empty_fields += 1
        
        if total_fields == 0:
            return 0.0
        
        return round((non_empty_fields / total_fields) * 100, 2)
    
    def calculate_batch_coverage(self) -> Dict:
        """
        计算数据集的覆盖率统计
        
        Returns:
            包含综合覆盖率、平均覆盖率、分布情况等信息的字典
        """
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 查询所有数据
            sql = f"SELECT * FROM {self.table_name}"
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    "dataset_id": self.dataset_id,
                    "display_name": self.metadata.get_display_name(),
                    "total_records": 0,
                    "comprehensive_coverage": 0.0,
                    "coverage_distribution": {
                        "90-100%": 0,
                        "80-90%": 0,
                        "70-80%": 0,
                        "60-70%": 0,
                        "50-60%": 0,
                        "40-50%": 0,
                        "30-40%": 0,
                        "20-30%": 0,
                        "10-20%": 0,
                        "0-10%": 0
                    },
                    "low_coverage_records": [],
                    "field_coverage": {},
                    "meets_threshold": False
                }
            
            total_records = len(rows)
            total_cells = 0
            non_empty_cells = 0
            
            # 字段覆盖率统计
            field_stats = {field: {"total": 0, "non_empty": 0} for field in self.data_fields}
            
            # 记录覆盖率统计
            row_coverages = []
            low_coverage_records = []
            
            # 覆盖率分布
            distribution = {
                "90-100%": 0, "80-90%": 0, "70-80%": 0, "60-70%": 0, "50-60%": 0,
                "40-50%": 0, "30-40%": 0, "20-30%": 0, "10-20%": 0, "0-10%": 0
            }
            
            for row in rows:
                row_coverage = self.calculate_row_coverage(row)
                row_coverages.append(row_coverage)
                
                # 分类统计（每10%一个区间）
                if row_coverage >= 90:
                    distribution["90-100%"] += 1
                elif row_coverage >= 80:
                    distribution["80-90%"] += 1
                elif row_coverage >= 70:
                    distribution["70-80%"] += 1
                elif row_coverage >= 60:
                    distribution["60-70%"] += 1
                elif row_coverage >= 50:
                    distribution["50-60%"] += 1
                elif row_coverage >= 40:
                    distribution["40-50%"] += 1
                elif row_coverage >= 30:
                    distribution["30-40%"] += 1
                elif row_coverage >= 20:
                    distribution["20-30%"] += 1
                elif row_coverage >= 10:
                    distribution["10-20%"] += 1
                else:
                    distribution["0-10%"] += 1
                
                # 记录低覆盖率的数据
                if row_coverage < self.threshold * 100:
                    # 获取标识字段（通常是'编号'）
                    identifier = row.get('编号', row.get('id', 'N/A'))
                    
                    # 包含完整行数据，以便前端动态展示列
                    record_data = {
                        "id": row.get('id'),
                        "identifier": identifier,
                        "coverage": row_coverage,
                        "full_data": row  # 包含原始数据
                    }
                    low_coverage_records.append(record_data)
                
                # 统计每个字段
                for field in self.data_fields:
                    if field in row:
                        field_stats[field]["total"] += 1
                        total_cells += 1
                        
                        if not self.is_empty_value(row[field]):
                            field_stats[field]["non_empty"] += 1
                            non_empty_cells += 1
            
            # 按覆盖率升序排序，取最低的20条
            low_coverage_records.sort(key=lambda x: x['coverage'])
            
            # 计算综合覆盖率
            comprehensive_coverage = round((non_empty_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0
            
            # 计算每个字段的覆盖率
            field_coverage = {}
            for field, stats in field_stats.items():
                if stats["total"] > 0:
                    field_coverage[field] = round((stats["non_empty"] / stats["total"]) * 100, 2)
                else:
                    field_coverage[field] = 0.0
            
            return {
                "dataset_id": self.dataset_id,
                "display_name": self.metadata.get_display_name(),
                "total_records": total_records,
                "total_fields": len(self.data_fields),
                "comprehensive_coverage": comprehensive_coverage,
                "coverage_distribution": distribution,
                "low_coverage_records": low_coverage_records,  # 返回所有低覆盖率记录
                "field_coverage": field_coverage,
                "threshold": self.threshold * 100,
                "meets_threshold": comprehensive_coverage >= self.threshold * 100
            }
            
        finally:
            conn.close()


def calculate_all_datasets_coverage() -> Dict:
    """
    计算所有数据集的覆盖率汇总
    
    Returns:
        总体覆盖率和各数据集详情
    """
    datasets = DatasetMetadata.list_all_datasets()
    
    batches_data = []
    total_records = 0
    total_cells = 0
    total_non_empty = 0
    
    for dataset_info in datasets:
        dataset_id = dataset_info['id']
        
        try:
            coverage_service = CoverageService(dataset_id)
            batch_coverage = coverage_service.calculate_batch_coverage()
            batches_data.append(batch_coverage)
            
            # 累计统计
            records = batch_coverage["total_records"]
            total_records += records
            
            if records > 0:
                # 每批次的单元格数 = 记录数 * 字段数
                metadata = DatasetMetadata(dataset_id)
                fields_count = len(metadata.get_coverage_calculation_fields())
                batch_cells = records * fields_count
                batch_non_empty = int((batch_coverage["comprehensive_coverage"] / 100) * batch_cells)
                
                total_cells += batch_cells
                total_non_empty += batch_non_empty
                
        except Exception as e:
            # 如果某个数据集出错，跳过
            print(f"计算 {dataset_id} 覆盖率失败: {e}")
            continue
    
    # 计算总体覆盖率
    overall_coverage = round((total_non_empty / total_cells) * 100, 2) if total_cells > 0 else 0.0
    
    return {
        "overall_coverage": overall_coverage,
        "total_records": total_records,
        "total_datasets": len(batches_data),
        "meets_threshold": overall_coverage >= 90.0,  # 默认90%阈值
        "datasets": batches_data
    }
