from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用配置
    APP_NAME: str = "焊接数据库系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # JWT配置
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-welding-2025"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_HOURS: int = 24
    
    # MySQL配置
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "root"
    MYSQL_PASSWORD: str = "1234"
    MYSQL_DATABASE: str = "metal_welding"
    MYSQL_POOL_SIZE: int = 5
    MYSQL_MAX_OVERFLOW: int = 10
    
    # MongoDB配置（可选）
    MONGODB_HOST: str = "localhost"
    MONGODB_PORT: int = 27017
    MONGODB_DATABASE: str = "welding"
    
    # 文件配置
    MAX_UPLOAD_SIZE: int = 52428800
    UPLOAD_DIR: str = "./uploads"
    
    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",  # Vite 默认端口
        "http://localhost:5174",  # Vite 备用端口
        "http://localhost:5175",  # Vite 备用端口
        "http://localhost:5176",  # Vite 备用端口
        "http://localhost:5177",  # Vite 备用端口
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",  # Vite 默认端口
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:8080"
    ]
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/app.log"
    
    # 批次配置
    BATCHES: dict = {
        "batch_1": "exp_data_batch_1",
        "batch_2": "exp_data_batch_2",
        "batch_3": "exp_data_batch_3",
        "batch_4": "exp_data_batch_4"
    }
    
    # 数据分类配置（16个字段）
    DATA_CATEGORIES: dict = {
        "物性": ["实验编号", "材料成分", "基体材料", "SiC体积分数", "密度"],
        "工艺": ["激光功率", "焊接速度", "离焦量", "保护气体流量"],
        "状态": ["温度场数据", "熔池图像", "传感器信号"],
        "性能": ["拉伸强度", "显微硬度", "焊缝宽度", "熔深"]
    }
    
    # 覆盖率阈值
    COVERAGE_THRESHOLD: float = 0.90
    
    # 空值列表
    NULL_VALUES: List[str] = [
        "", " ", "N/A", "n/a", "NA", "na", "-", 
        "unknown", "Unknown", "UNKNOWN", 
        "null", "Null", "NULL", "none", "None"
    ]
    
    class Config:
        env_file = None  # 禁用.env文件加载，使用默认值
        case_sensitive = True

settings = Settings()
