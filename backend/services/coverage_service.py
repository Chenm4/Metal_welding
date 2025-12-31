"""数据覆盖率计算服务"""
import pymysql
from typing import Dict, List
from backend.config import Settings


settings = Settings()


class CoverageService:
    """覆盖率计算服务"""
    
    def __init__(self):
        self.settings = settings
        # 34个数据字段（排除id和审计字段）
        self.data_fields = [
            '编号', '物性_材料', '工艺', '接头类型', '焊丝',
            '物性_基体材料_合金牌号', '物性_SiC增强体_体积分数', '物性_SiC增强体_形状',
            '物性_SiC增强体_尺寸_um', '物性_基材厚度_mm', '物性_物理性能_密度_g_cm3',
            '物性_物理性能_热导率', '物性_力学性能_拉伸强度_MPa', '物性_力学性能_屈服强度_MPa',
            '物性_力学性能_伸长率', '工艺_激光焊接_激光功率_W', '工艺_激光焊接_焊接速度_mm_s',
            '工艺_激光焊接_离焦量_mm', '工艺_激光焊接_保护气体流量_L_min',
            '工艺_激光焊接_激光光斑直径_mm', '工艺_激光焊接_能量密度_J_mm2',
            '状态_实时监测_焊接温度_℃', '状态_实时监测_冷却速度_℃_s',
            '状态_实时监测_熔池尺寸_长度_mm', '状态_实时监测_熔池尺寸_宽度_mm',
            '状态_实时监测_传感信号_等离子体光强度', '状态_实时监测_传感信号_声发射信号',
            '性能_外观质量_表面缺陷类型', '性能_焊缝几何_焊缝宽度_mm', '性能_焊缝几何_熔深_mm',
            '性能_焊缝几何_熔宽比', '性能_显微组织_界面特征',
            '性能_拉伸性能（温度23℃）拉伸强度_MPa',
            '性能_拉伸性能（温度23℃）断后伸长率%'
        ]
    
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
        
        Args:
            row: 数据记录字典
            
        Returns:
            覆盖率（0-100）
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
    
    def calculate_batch_coverage(self, batch_id: int) -> Dict:
        """
        计算指定批次的覆盖率统计
        
        包括:
        1. 综合覆盖率 (整个批次所有数据项的填充率)
        2. 每条记录的覆盖率统计
        3. 覆盖率分布情况
        
        Args:
            batch_id: 批次ID (1-4)
            
        Returns:
            {
                "batch_id": 1,
                "total_records": 160,
                "total_fields": 37,
                "comprehensive_coverage": 85.5,  # 综合覆盖率
                "average_coverage": 87.2,         # 平均覆盖率
                "coverage_distribution": {        # 覆盖率分布
                    "90-100%": 120,
                    "80-90%": 30,
                    "70-80%": 8,
                    "below_70%": 2
                },
                "low_coverage_records": [         # 低覆盖率记录（<90%）
                    {"id": 1, "编号": "xxx", "coverage": 75.5},
                    ...
                ],
                "field_coverage": {               # 每个字段的覆盖率
                    "编号": 100.0,
                    "物性_材料": 98.5,
                    ...
                }
            }
        """
        table_name = self.get_table_name(batch_id)
        conn = self.get_connection()
        
        try:
            cursor = conn.cursor()
            
            # 查询所有数据
            sql = f"SELECT * FROM {table_name}"
            cursor.execute(sql)
            rows = cursor.fetchall()
            
            if not rows:
                return {
                    "batch_id": batch_id,
                    "total_records": 0,
                    "comprehensive_coverage": 0.0,
                    "average_coverage": 0.0,
                    "coverage_distribution": {"90-100%": 0, "80-90%": 0, "70-80%": 0, "below_70%": 0},
                    "low_coverage_records": [],
                    "field_coverage": {}
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
            distribution = {"90-100%": 0, "80-90%": 0, "70-80%": 0, "below_70%": 0}
            
            for row in rows:
                row_coverage = self.calculate_row_coverage(row)
                row_coverages.append(row_coverage)
                
                # 分类统计
                if row_coverage >= 90:
                    distribution["90-100%"] += 1
                elif row_coverage >= 80:
                    distribution["80-90%"] += 1
                elif row_coverage >= 70:
                    distribution["70-80%"] += 1
                else:
                    distribution["below_70%"] += 1
                
                # 记录低覆盖率的数据
                if row_coverage < self.settings.COVERAGE_THRESHOLD * 100:
                    low_coverage_records.append({
                        "id": row.get('id'),
                        "编号": row.get('编号', 'N/A'),
                        "coverage": row_coverage
                    })
                
                # 统计每个字段
                for field in self.data_fields:
                    if field in row:
                        field_stats[field]["total"] += 1
                        total_cells += 1
                        
                        if not self.is_empty_value(row[field]):
                            field_stats[field]["non_empty"] += 1
                            non_empty_cells += 1
            
            # 计算综合覆盖率
            comprehensive_coverage = round((non_empty_cells / total_cells) * 100, 2) if total_cells > 0 else 0.0
            
            # 计算平均覆盖率
            average_coverage = round(sum(row_coverages) / len(row_coverages), 2) if row_coverages else 0.0
            
            # 计算每个字段的覆盖率
            field_coverage = {}
            for field, stats in field_stats.items():
                if stats["total"] > 0:
                    field_coverage[field] = round((stats["non_empty"] / stats["total"]) * 100, 2)
                else:
                    field_coverage[field] = 0.0
            
            return {
                "batch_id": batch_id,
                "total_records": total_records,
                "comprehensive_coverage": comprehensive_coverage,
                "average_coverage": average_coverage,
                "coverage_distribution": distribution,
                "low_coverage_records": low_coverage_records[:20],  # 最多返回20条
                "field_coverage": field_coverage,
                "meets_threshold": comprehensive_coverage >= self.settings.COVERAGE_THRESHOLD * 100
            }
            
        finally:
            conn.close()
    
    def calculate_all_batches_coverage(self) -> Dict:
        """
        计算所有批次的覆盖率汇总（动态获取所有数据集表）
        
        Returns:
            {
                "overall_coverage": 85.5,
                "batches": [
                    {"batch_id": 1, "comprehensive_coverage": 85.5, ...},
                    ...
                ]
            }
        """
        # 动态获取所有数据集表
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'exp_data_%'")
            tables = cursor.fetchall()
            dataset_tables = [list(table.values())[0] for table in tables]
        finally:
            conn.close()
        
        batches_data = []
        total_records = 0
        total_cells = 0
        total_non_empty = 0
        
        for table_name in dataset_tables:
            # 提取batch_id（从表名exp_data_batch_1中提取1）
            dataset_id = table_name.replace('exp_data_', '')
            if dataset_id.startswith('batch_'):
                try:
                    batch_id = int(dataset_id.replace('batch_', ''))
                except ValueError:
                    continue
            else:
                continue  # 跳过非batch格式的表
            
            try:
                batch_coverage = self.calculate_batch_coverage(batch_id)
                batches_data.append(batch_coverage)
                
                # 累计统计
                records = batch_coverage["total_records"]
                total_records += records
                
                if records > 0:
                    # 每批次的单元格数 = 记录数 * 字段数
                    batch_cells = records * len(self.data_fields)
                    batch_non_empty = int((batch_coverage["comprehensive_coverage"] / 100) * batch_cells)
                    
                    total_cells += batch_cells
                    total_non_empty += batch_non_empty
                    
            except Exception as e:
                # 如果某个批次不存在或出错，跳过
                continue
        
        # 计算总体覆盖率
        overall_coverage = round((total_non_empty / total_cells) * 100, 2) if total_cells > 0 else 0.0
        
        return {
            "overall_coverage": overall_coverage,
            "total_records": total_records,
            "meets_threshold": overall_coverage >= self.settings.COVERAGE_THRESHOLD * 100,
            "batches": batches_data
        }
