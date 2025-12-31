"""
日志工具模块
提供统一的日志配置和管理功能

功能：
1. 同时输出到控制台和文件
2. 文件名和行号可点击跳转
3. 彩色日志输出（控制台）
4. 自动按日期轮转日志文件
5. 不同级别日志分离

"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import os

# 日志配置常量
LOG_DIR = Path(__file__).parent.parent.parent / "logs"  # 项目根目录/logs
LOG_FORMAT = "%(asctime)s | %(levelname)-4s | %(filename)s:%(lineno)d | %(funcName)s() | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ANSI颜色代码（用于终端彩色输出）
COLOR_CODES = {
    'DEBUG': '\033[36m',      # 青色
    'INFO': '\033[32m',       # 绿色
    'WARNING': '\033[33m',    # 黄色
    'ERROR': '\033[31m',      # 红色
    'CRITICAL': '\033[35m',   # 紫色
    'RESET': '\033[0m'        # 重置
}


class ColoredFormatter(logging.Formatter):
    """
    彩色日志格式化器
    
    为不同级别的日志添加颜色（仅在控制台输出时）
    保持文件日志为纯文本
    """

    def format(self, record):
        """
        格式化日志记录，添加颜色代码
        
        Args:
            record: 日志记录对象
            
        Returns:
            格式化后的日志字符串（带颜色）
        """
        # 获取原始格式化结果
        log_message = super().format(record)
        
        # 添加颜色代码
        color = COLOR_CODES.get(record.levelname, COLOR_CODES['RESET'])
        colored_message = f"{color}{log_message}{COLOR_CODES['RESET']}"
        
        return colored_message


def setup_logger(
    name: str = "metal_welding",
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_to_console: bool = True,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    设置并返回配置好的日志记录器
    
    功能：
    - 同时输出到控制台和文件（可选）
    - 控制台输出带颜色
    - 文件按大小自动轮转
    - 不同日期的日志分开存储
    - 文件名:行号格式支持IDE点击跳转
    
    Args:
        name: 日志记录器名称，默认"metal_welding"
        level: 日志级别，默认INFO
        log_to_file: 是否输出到文件，默认True
        log_to_console: 是否输出到控制台，默认True
        max_file_size: 单个日志文件最大大小（字节），默认10MB
        backup_count: 保留的日志文件数量，默认5个
    
    Returns:
        配置好的Logger对象
    
    使用示例：
        from backend.utils.logger import setup_logger
        
        logger = setup_logger(__name__)
        logger.info("这是一条信息日志")
        logger.error("这是一条错误日志", exc_info=True)
    """
    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 避免重复添加处理器（如果已经配置过）
    if logger.handlers:
        return logger
    
    # 创建日志目录（如果不存在）
    if log_to_file:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        
        # 按日期创建子目录
        today = datetime.now().strftime("%Y-%m-%d")
        daily_log_dir = LOG_DIR / today
        daily_log_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== 控制台处理器 ====================
    if log_to_console:
        # 创建控制台处理器（输出到标准输出）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        
        # 使用彩色格式化器
        console_formatter = ColoredFormatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        console_handler.setFormatter(console_formatter)
        
        # 添加到日志记录器
        logger.addHandler(console_handler)
    
    # ==================== 文件处理器 ====================
    if log_to_file:
        # 1. 所有日志文件（INFO及以上）
        all_log_file = daily_log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            all_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        file_formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        # 2. 错误日志文件（ERROR及以上）
        error_log_file = daily_log_dir / f"error_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        logger.addHandler(error_handler)
        
        # 3. 访问日志文件（专门记录API请求）
        access_log_file = daily_log_dir / f"access_{datetime.now().strftime('%Y%m%d')}.log"
        access_handler = RotatingFileHandler(
            access_log_file,
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        access_handler.setLevel(logging.INFO)
        # 访问日志使用简化格式
        access_format = "%(asctime)s | %(message)s"
        access_formatter = logging.Formatter(access_format, datefmt=DATE_FORMAT)
        access_handler.setFormatter(access_formatter)
        
        # 添加过滤器，只记录包含特定标记的日志
        access_handler.addFilter(lambda record: hasattr(record, 'access_log'))
        logger.addHandler(access_handler)
    
    return logger


def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志记录器的便捷方法
    
    如果尚未配置，会自动调用setup_logger()进行配置
    如果已配置，直接返回现有的logger
    
    Args:
        name: 日志记录器名称，默认使用调用模块的__name__
    
    Returns:
        Logger对象
    
    使用示例：
        from backend.utils.logger import get_logger
        
        logger = get_logger(__name__)
        logger.debug("调试信息")
        logger.info("程序启动成功")
        logger.warning("配置文件缺失，使用默认值")
        logger.error("数据库连接失败", exc_info=True)
    """
    if name is None:
        # 自动获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'metal_welding')
    
    logger = logging.getLogger(name)
    
    # 如果还没有配置处理器，自动配置
    if not logger.handlers:
        logger = setup_logger(name)
    
    return logger


def log_function_call(func):
    """
    函数调用日志装饰器
    
    自动记录函数的调用、参数、返回值和执行时间
    适用于需要追踪的关键业务函数
    
    使用示例：
        from backend.utils.logger import log_function_call, get_logger
        
        logger = get_logger(__name__)
        
        @log_function_call
        def calculate_coverage(dataset_id: str) -> float:
            # 函数逻辑
            return 95.5
    """
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 记录函数调用开始
        logger.debug(f"调用函数: {func.__name__}")
        logger.debug(f"  参数 args: {args}")
        logger.debug(f"  参数 kwargs: {kwargs}")
        
        start_time = time.time()
        
        try:
            # 执行函数
            result = func(*args, **kwargs)
            
            # 记录执行时间
            elapsed = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行成功，耗时: {elapsed:.3f}秒")
            
            return result
            
        except Exception as e:
            # 记录异常
            elapsed = time.time() - start_time
            logger.error(
                f"函数 {func.__name__} 执行失败，耗时: {elapsed:.3f}秒，"
                f"异常: {type(e).__name__}: {str(e)}",
                exc_info=True
            )
            raise
    
    return wrapper


def log_api_request(method: str, path: str, status_code: int, duration: float, user: str = None):
    """
    记录API请求日志（专用于访问日志）
    
    Args:
        method: HTTP方法（GET、POST等）
        path: 请求路径
        status_code: 响应状态码
        duration: 请求处理时长（秒）
        user: 用户名（可选）
    
    使用示例：
        log_api_request("GET", "/api/experimental-data/batch_1", 200, 0.045, "admin")
    """
    logger = get_logger("metal_welding.access")
    
    # 添加access_log标记，让访问日志处理器识别
    extra = {'access_log': True}
    
    # 格式化日志消息
    user_info = f" | User: {user}" if user else ""
    message = f"{method:6s} {path:50s} | Status: {status_code} | {duration*1000:.2f}ms{user_info}"
    
    # 根据状态码选择日志级别
    if status_code >= 500:
        logger.error(message, extra=extra)
    elif status_code >= 400:
        logger.warning(message, extra=extra)
    else:
        logger.info(message, extra=extra)


# 创建默认的全局logger
default_logger = setup_logger()


if __name__ == "__main__":
    """
    测试日志功能
    
    运行此文件可测试各种日志级别和格式
    """
    # 创建测试logger
    test_logger = get_logger("test")
    
    print("\n" + "="*80)
    print("日志系统测试")
    print("="*80 + "\n")
    
    # 测试各种日志级别
    test_logger.debug("这是DEBUG级别日志 - 详细的调试信息")
    test_logger.info("这是INFO级别日志 - 一般信息")
    test_logger.warning("这是WARNING级别日志 - 警告信息")
    test_logger.error("这是ERROR级别日志 - 错误信息")
    test_logger.critical("这是CRITICAL级别日志 - 严重错误")
    
    # 测试异常日志
    try:
        1 / 0
    except Exception as e:
        test_logger.error("捕获到异常", exc_info=True)
    
    # 测试API请求日志
    log_api_request("GET", "/api/experimental-data/batch_1", 200, 0.045, "admin")
    log_api_request("POST", "/api/auth/login", 401, 0.012)
    log_api_request("DELETE", "/api/experimental-data/batch_1/123", 500, 0.123, "admin")
    
    print(f"\n日志文件已保存到: {LOG_DIR}")
    print(f"今日日志目录: {LOG_DIR / datetime.now().strftime('%Y-%m-%d')}")
