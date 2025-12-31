"""生成数据集元数据配置文件

本脚本用于自动扫描数据库中的所有实验数据表，
分析表结构，生成统一的元数据配置文件（dataset_metadata.json）。

功能：
1. 动态发现所有exp_data_开头的数据表
2. 分析每个表的字段类型和分类
3. 生成JSON格式的元数据配置
4. 支持无限数量的数据集扩展

使用方式：
    cd backend/scripts
    python generate_metadata.py
"""

import pymysql
import json
from pathlib import Path
import sys

# 添加父目录到Python路径，以便导入logger模块
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.logger import get_logger
from config import settings

# 初始化日志记录器
logger = get_logger(__name__)

# 审计字段列表（系统自动管理，不参与业务逻辑）
AUDIT_FIELDS = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by', 'deleted_at', 'is_deleted', 'version']

def get_database_connection():
    """
    创建并返回MySQL数据库连接
    
    功能说明：
    1. 连接到本地MySQL服务器的数据库
    2. 使用utf8mb4字符集，支持完整的Unicode字符（包括emoji）
    3. 连接失败时记录错误日志并抛出异常
    4. 返回的连接对象需要在使用完毕后手动关闭
    5. 建议使用with语句或try-finally确保连接关闭
    
    Returns:
        pymysql.connections.Connection: MySQL数据库连接对象
    
    Raises:
        Exception: 数据库连接失败时抛出异常
    
    使用示例：
        conn = get_database_connection()
        try:
            cursor = conn.cursor()
            # 执行数据库操作
        finally:
            conn.close()
    """
    try:
        logger.info("正在连接MySQL数据库...")
        conn = pymysql.connect(
            host=settings.MYSQL_HOST,
            port=settings.MYSQL_PORT,
            user=settings.MYSQL_USER,
            password=settings.MYSQL_PASSWORD,
            database=settings.MYSQL_DATABASE,
            charset='utf8mb4'
        )
        logger.info(f"✓ 数据库连接成功: {settings.MYSQL_DATABASE}@{settings.MYSQL_HOST}")
        return conn
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {str(e)}", exc_info=True)
        raise


def get_table_columns(conn, table_name):
    """
    获取指定数据库表的所有列信息
    
    功能说明：
    1. 执行SHOW COLUMNS查询获取表结构
    2. 提取每列的名称（Field）和数据类型（Type）
    3. 过滤掉系统字段和审计字段
    4. 返回字段名和类型的元组列表
    5. 用于后续的字段类型推断和元数据生成
    
    Args:
        conn (pymysql.connections.Connection): 数据库连接对象
        table_name (str): 要查询的表名，如'exp_data_batch_1'
    
    Returns:
        List[Tuple[str, str]]: 字段列表，每个元素为(字段名, 字段类型)的元组
                              例如: [('编号', 'varchar(50)'), ('物性_材料', 'varchar(100)')]
    
    Raises:
        Exception: 查询失败时抛出异常
    
    使用示例：
        columns = get_table_columns(conn, 'exp_data_batch_1')
        for col_name, col_type in columns:
            print(f"{col_name}: {col_type}")
    """
    try:
        cursor = conn.cursor()
        logger.debug(f"查询表结构: {table_name}")
        
        # 执行SHOW COLUMNS查询
        cursor.execute(f"SHOW COLUMNS FROM {table_name}")
        columns = cursor.fetchall()
        
        # 提取字段名和类型（第0列是Field，第1列是Type）
        result = [(col[0], col[1]) for col in columns]
        logger.debug(f"表 {table_name} 共有 {len(result)} 个字段")
        
        return result
    except Exception as e:
        logger.error(f"✗ 查询表结构失败: {table_name}, 错误: {str(e)}")
        raise

def categorize_field(field_name):
    """
    根据字段名前缀自动判断字段分类
    
    功能说明：
    1. 分析字段名的前缀（如"物性_"、"工艺_"等）
    2. 根据预定义的分类规则返回相应类别
    3. 支持四种主要分类：物性、工艺、状态、性能
    4. 不符合任何前缀的字段归类为"其他"
    5. 前端可根据分类信息对字段进行分组显示
    
    Args:
        field_name (str): 字段名，如"物性_材料"、"工艺_激光功率"
    
    Returns:
        str: 字段分类，可能的值：
             - '物性': 材料物理性质相关字段
             - '工艺': 焊接工艺参数相关字段
             - '状态': 过程状态监测相关字段
             - '性能': 产品性能指标相关字段
             - '其他': 无明确前缀的字段
    
    使用示例：
        category = categorize_field("物性_材料")
        # 返回: "物性"
        
        category = categorize_field("编号")
        # 返回: "其他"
    """
    # 按前缀匹配分类
    if field_name.startswith('物性_'):
        return '物性'
    elif field_name.startswith('工艺_'):
        return '工艺'
    elif field_name.startswith('状态_'):
        return '状态'
    elif field_name.startswith('性能_'):
        return '性能'
    
    # 默认分类
    return '其他'

def infer_type(mysql_type):
    """
    根据MySQL字段类型推断前端使用的抽象类型
    
    功能说明：
    1. 将MySQL的具体类型（varchar、int、datetime等）映射到抽象类型
    2. 抽象类型用于前端表单验证和数据展示
    3. 支持整数、浮点数、日期时间、字符串四种基本类型
    4. 不区分大小写，统一转换为小写后匹配
    5. 默认类型为string，确保兼容性
    
    Args:
        mysql_type (str): MySQL字段类型，如'varchar(100)'、'int(11)'、'datetime'
    
    Returns:
        str: 抽象类型，可能的值：
             - 'integer': 整数类型（int、tinyint、bigint等）
             - 'float': 浮点数类型（float、double、decimal等）
             - 'datetime': 日期时间类型（date、datetime、timestamp等）
             - 'string': 字符串类型（varchar、text、char等，默认类型）
    
    使用示例：
        type1 = infer_type('varchar(100)')  # 返回: 'string'
        type2 = infer_type('int(11)')       # 返回: 'integer'
        type3 = infer_type('decimal(10,2)') # 返回: 'float'
        type4 = infer_type('datetime')      # 返回: 'datetime'
    """
    # 转换为小写，便于匹配
    mysql_type = mysql_type.lower()
    
    # 整数类型判断
    if 'int' in mysql_type:
        return 'integer'
    
    # 浮点数类型判断
    elif 'float' in mysql_type or 'double' in mysql_type or 'decimal' in mysql_type:
        return 'float'
    
    # 日期时间类型判断
    elif 'date' in mysql_type or 'time' in mysql_type:
        return 'datetime'
    
    # 默认为字符串类型
    else:
        return 'string'



def get_all_dataset_tables(conn):
    """
    获取数据库中所有实验数据表（动态发现）
    
    功能说明：
    1. 使用SHOW TABLES LIKE模式匹配所有exp_data_开头的表
    2. 支持无限数量的数据集（batch_1到batch_N，或任意命名）
    3. 不再硬编码批次数量，完全动态发现
    4. 返回表名列表，用于后续遍历处理
    5. 这是实现零硬编码、可扩展架构的关键步骤
    
    Args:
        conn (pymysql.connections.Connection): 数据库连接对象
    
    Returns:
        List[str]: 数据表名列表，如['exp_data_batch_1', 'exp_data_batch_2', 'exp_data_custom']
    
    Raises:
        Exception: 查询失败时抛出异常
    
    使用示例：
        tables = get_all_dataset_tables(conn)
        logger.info(f"发现 {len(tables)} 个数据集表")
        for table in tables:
            process_table(table)
    """
    try:
        cursor = conn.cursor()
        logger.info("正在扫描数据库中的数据集表...")
        
        # 使用LIKE模式匹配所有exp_data_开头的表
        cursor.execute("SHOW TABLES LIKE 'exp_data_%'")
        tables = cursor.fetchall()
        
        # 提取表名（fetchall返回的是元组列表）
        table_names = [table[0] for table in tables]
        
        logger.info(f"✓ 发现 {len(table_names)} 个数据集表: {', '.join(table_names)}")
        return table_names
        
    except Exception as e:
        logger.error(f"✗ 扫描数据表失败: {str(e)}", exc_info=True)
        raise


def process_dataset_table(conn, table_name, metadata):
    """
    处理单个数据集表，生成其元数据配置
    
    功能说明：
    1. 从表名提取dataset_id（如exp_data_batch_1 → batch_1）
    2. 生成display_name和description（支持batch和自定义命名）
    3. 获取表的所有列信息，排除审计字段
    4. 推断每个字段的类型和分类
    5. 构建完整的元数据配置对象
    
    Args:
        conn (pymysql.connections.Connection): 数据库连接对象
        table_name (str): 数据库表名，如'exp_data_batch_1'
        metadata (dict): 元数据字典，函数会将新数据集配置添加到其中
    
    Returns:
        None: 直接修改metadata字典，无返回值
    
    Raises:
        Exception: 处理失败时记录错误日志并继续处理下一个表
    
    使用示例：
        metadata = {"datasets": {}}
        process_dataset_table(conn, 'exp_data_batch_1', metadata)
        # metadata['datasets']['batch_1'] 现在包含完整配置
    """
    try:
        logger.info(f"正在处理: {table_name}...")
        
        # 提取dataset_id（从表名中移除exp_data_前缀）
        # 例如: exp_data_batch_1 → batch_1, exp_data_custom → custom
        dataset_id = table_name.replace('exp_data_', '')
        
        # 生成显示名称和描述（智能识别batch格式）
        if dataset_id.startswith('batch_'):
            # 批次格式：batch_1 → 第1批实验数据
            batch_num = dataset_id.replace('batch_', '')
            display_name = f"第{batch_num}批实验数据"
            description = f"批次{batch_num}的激光焊接实验数据"
        else:
            # 自定义格式：custom → custom实验数据
            display_name = f"{dataset_id}实验数据"
            description = f"{dataset_id}的激光焊接实验数据"
        
        # 获取表的所有列信息
        columns = get_table_columns(conn, table_name)
        
        # 分析字段，生成字段列表
        data_fields = []
        for col_name, col_type in columns:
            # 跳过审计字段（系统自动管理）
            if col_name in AUDIT_FIELDS:
                logger.debug(f"  跳过审计字段: {col_name}")
                continue
            
            # 推断字段分类和类型
            category = categorize_field(col_name)
            field_type = infer_type(col_type)
            
            # 构建字段信息对象
            field_info = {
                "name": col_name,
                "type": field_type,
                "nullable": True,
                "category": category
            }
            data_fields.append(field_info)
            logger.debug(f"  字段: {col_name} ({field_type}) - 分类: {category}")
        
        # 注意：不再生成 searchable_fields 配置
        # 所有 data_fields 默认都可搜索，由代码动态获取
        # 这样避免了配置冗余，所有字段自动支持搜索
        
        # 构建完整的数据集配置
        dataset_config = {
            "table_name": table_name,
            "display_name": display_name,
            "description": description,
            "fields": {
                "data_fields": data_fields,
                "required_fields": ["编号"] if "编号" in [f["name"] for f in data_fields] else [],
                "audit_fields": ["created_at", "updated_at", "created_by", "updated_by"]
            },
            "coverage": {
                "threshold": 0.9,
                "exclude_from_calculation": AUDIT_FIELDS
            }
        }
        
        # 添加到元数据字典
        metadata["datasets"][dataset_id] = dataset_config
        
        logger.info(f"✓ {table_name}: {len(data_fields)} 个数据字段")
        
    except Exception as e:
        logger.error(f"✗ {table_name} 处理失败: {str(e)}", exc_info=True)
        # 不中断整个流程，继续处理下一个表


def save_metadata_to_file(metadata, output_path):
    """
    将元数据配置保存到JSON文件
    
    功能说明：
    1. 创建输出目录（如果不存在）
    2. 将Python字典序列化为格式化的JSON字符串
    3. 使用UTF-8编码写入文件，确保中文正常显示
    4. 使用indent=2使JSON文件易读（便于手动调整）
    5. 记录保存结果和统计信息
    
    Args:
        metadata (dict): 完整的元数据字典，包含所有数据集配置
        output_path (Path): 输出文件路径，通常为backend/config/dataset_metadata.json
    
    Returns:
        bool: 保存成功返回True，失败返回False
    
    Raises:
        Exception: 文件写入失败时抛出异常
    
    使用示例：
        metadata = {"datasets": {...}}
        output_path = Path(__file__).parent.parent / 'config' / 'dataset_metadata.json'
        save_metadata_to_file(metadata, output_path)
    """
    try:
        # 确保输出目录存在
        output_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"准备保存元数据配置到: {output_path}")
        
        # 序列化为JSON（格式化，易读）
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 统计信息
        dataset_count = len(metadata['datasets'])
        total_fields = sum(
            len(ds['fields']['data_fields']) 
            for ds in metadata['datasets'].values()
        )
        
        logger.info("=" * 60)
        logger.info("✓ 元数据配置生成完成！")
        logger.info("=" * 60)
        logger.info(f"输出文件: {output_path}")
        logger.info(f"数据集数量: {dataset_count} 个")
        logger.info(f"总字段数: {total_fields} 个")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ 保存元数据配置失败: {str(e)}", exc_info=True)
        return False


def main():
    """
    主函数：协调整个元数据生成流程
    
    功能说明：
    1. 初始化日志系统，记录执行过程
    2. 连接MySQL数据库
    3. 动态发现所有实验数据表
    4. 遍历每个表，生成元数据配置
    5. 保存配置到JSON文件
    
    执行流程：
        1. 打印启动横幅
        2. 建立数据库连接
        3. 扫描exp_data_*表
        4. 逐个处理表结构
        5. 汇总生成JSON文件
        6. 关闭数据库连接
        7. 输出完成信息
    
    Returns:
        None
    
    使用方式：
        cd backend/scripts
        python generate_metadata.py
    """
    # 打印启动横幅
    logger.info("=" * 60)
    logger.info("数据集元数据生成工具")
    logger.info("=" * 60)
    
    conn = None
    try:
        # 1. 连接数据库
        conn = get_database_connection()
        
        # 2. 动态发现所有数据集表
        dataset_tables = get_all_dataset_tables(conn)
        
        if not dataset_tables:
            logger.warning("⚠ 未发现任何数据集表（exp_data_*）")
            return
        
        # 3. 初始化元数据结构
        metadata = {"datasets": {}}
        
        # 4. 遍历处理每个表
        logger.info("")
        logger.info("开始分析字段结构...")
        for table_name in dataset_tables:
            process_dataset_table(conn, table_name, metadata)
        
        # 5. 保存到配置文件
        logger.info("")
        config_path = Path(__file__).parent.parent / 'config' / 'dataset_metadata.json'
        save_metadata_to_file(metadata, config_path)
        
    except Exception as e:
        logger.error(f"✗ 程序执行失败: {str(e)}", exc_info=True)
        
    finally:
        # 6. 确保关闭数据库连接
        if conn:
            conn.close()
            logger.debug("数据库连接已关闭")


if __name__ == "__main__":
    main()

