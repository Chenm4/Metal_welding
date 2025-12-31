"""
FastAPI应用入口

此文件是整个后端应用的启动入口，负责：
1. 创建FastAPI应用实例
2. 配置CORS跨域中间件
3. 注册所有路由模块
4. 提供健康检查接口
5. 配置请求/响应日志中间件
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import time
from datetime import datetime
from backend.config import Settings
from backend.routes import auth
from backend.routes.experimental import data_routes
from backend.utils.logger import get_logger, log_api_request

# ==================== 日志初始化 ====================
# 创建日志记录器 - 使用模块名作为logger名称，便于追踪日志来源
logger = get_logger(__name__)
logger.info("="*80)
logger.info(f"应用启动 - 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
logger.info("="*80)

# ==================== 配置加载 ====================
# Settings类会自动读取.env文件和环境变量
settings = Settings()
logger.info(f"✓ 配置加载完成")
logger.info(f"  - 应用名称: {settings.APP_NAME}")
logger.info(f"  - 应用版本: {settings.APP_VERSION}")
logger.info(f"  - 数据库: {settings.MYSQL_DATABASE}")
logger.info(f"  - 调试模式: {settings.DEBUG}")
logger.info(f"  - CORS源: {settings.CORS_ORIGINS}")

# ==================== FastAPI应用创建 ====================
# 创建FastAPI应用实例，配置API文档路径和应用元信息
logger.info("正在创建FastAPI应用实例...")
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于元数据驱动的实验数据管理系统 - 支持动态数据集创建和零硬编码扩展",
    docs_url=None,           # 使用自定义Swagger UI
    redoc_url=None,          # 使用自定义ReDoc
    openapi_url="/api/openapi.json"  # OpenAPI Schema路径
)
logger.info("✓ FastAPI应用实例创建成功")

# ==================== 静态文件挂载 ====================
# 挂载静态文件目录（Swagger UI和ReDoc资源）
logger.info("正在挂载静态文件目录...")
app.mount("/static", StaticFiles(directory="static"), name="static")
logger.info("✓ 静态文件目录挂载成功: /static")

# ==================== 中间件配置 ====================
# 1. 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    HTTP请求日志中间件
    
    功能：
    1. 记录每个API请求的详细信息
    2. 计算请求处理时间
    3. 记录响应状态码
    4. 提取用户信息（如果已认证）
    
    日志格式：
    - 请求方法和路径
    - 客户端IP地址
    - 请求处理时长
    - 响应状态码
    - 用户名（如果已登录）
    """
    # 记录请求开始时间
    start_time = time.time()
    
    # 提取请求信息
    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"
    
    # 记录请求开始
    logger.info(f"→ 收到请求: {method} {path} | IP: {client_ip}")
    
    try:
        # 处理请求
        response = await call_next(request)
        
        # 计算处理时间
        duration = time.time() - start_time
        status_code = response.status_code
        
        # 尝试提取用户信息（从request.state中，如果路由设置了）
        user = getattr(request.state, "user", None)
        username = user.get("username") if user else None
        
        # 记录API访问日志
        log_api_request(method, path, status_code, duration, username)
        
        # 记录响应完成
        status_emoji = "✓" if status_code < 400 else "✗"
        logger.info(
            f"{status_emoji} 响应完成: {method} {path} | "
            f"状态: {status_code} | 耗时: {duration*1000:.2f}ms"
        )
        
        return response
        
    except Exception as e:
        # 记录异常
        duration = time.time() - start_time
        logger.error(
            f"✗ 请求处理失败: {method} {path} | "
            f"耗时: {duration*1000:.2f}ms | "
            f"异常: {type(e).__name__}: {str(e)}",
            exc_info=True
        )
        raise

# 2. CORS跨域中间件配置
logger.info("正在配置CORS跨域中间件...")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,     # 允许的源（从配置读取）
    allow_credentials=True,                  # 允许携带凭证（cookies、authorization headers）
    allow_methods=["*"],                     # 允许所有HTTP方法
    allow_headers=["*"],                     # 允许所有请求头
)
logger.info(f"✓ CORS中间件配置完成 - 允许的源: {settings.CORS_ORIGINS}")

# ==================== 路由注册 ====================

# 1. 认证路由（/api/auth/*）
logger.info("  - 注册认证路由: /api/auth")
app.include_router(auth.router)

# 2. 实验数据路由（/api/experimental-data/*）
logger.info("  - 注册实验数据路由: /api/experimental-data")
app.include_router(data_routes.router)

logger.info("✓ 所有路由注册完成")

# ==================== API端点定义 ====================

@app.get("/", tags=["根路径"])
async def root():
    """
    根路径接口
    
    返回API基本信息和文档链接
    用于快速检查API是否正常运行
    
    Returns:
        dict: 包含应用信息和文档链接
    
    错误码：
    - 500: 服务器内部错误
    """
    try:
        logger.debug("访问根路径 /")
        return {
            "message": "焊接数据库系统API",
            "version": settings.APP_VERSION,
            "docs": "/api/docs",       # Swagger UI文档
            "redoc": "/api/redoc",     # ReDoc文档
            "status": "running"
        }
    except Exception as e:
        logger.error(f"根路径访问失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"服务器内部错误: {str(e)}"
        )


@app.get("/api/health", tags=["健康检查"])
async def health_check():
    """
    健康检查接口
    
    用于监控和负载均衡的健康检查
    返回服务状态、名称和版本信息
    
    Returns:
        dict: 健康状态信息
    
    错误码：
    - 503: 服务不可用（数据库连接失败等）
    - 500: 服务器内部错误
    """
    try:
        logger.debug("健康检查请求")
        
        # 检查数据库连接
        from backend.utils.database import get_db_connection
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            conn.close()
            db_status = "connected"
            logger.debug("数据库连接正常")
        except Exception as db_error:
            logger.error(f"数据库连接失败: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"数据库连接失败: {str(db_error)}"
            )
        
        return {
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "database": db_status,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康检查失败: {str(e)}"
        )


@app.get("/api/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """
    自定义Swagger UI文档页面
    
    使用本地静态文件提供Swagger UI，避免依赖CDN
    提供交互式API文档，可直接测试接口
    
    Returns:
        HTMLResponse: Swagger UI HTML页面
    
    错误码：
    - 404: 静态文件不存在
    - 500: 文档加载失败
    """
    try:
        logger.debug("加载Swagger UI文档")
        
        # 检查静态文件是否存在
        import os
        swagger_path = "static/swagger-ui/dist/swagger-ui.css"
        if not os.path.exists(swagger_path):
            logger.error(f"Swagger UI静态文件不存在: {swagger_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Swagger UI静态文件不存在，请确保已正确安装"
            )
        
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="/static/swagger-ui/dist/swagger-ui.css">
    <link rel="icon" type="image/png" href="/static/swagger-ui/dist/favicon-32x32.png" sizes="32x32">
    <link rel="icon" type="image/png" href="/static/swagger-ui/dist/favicon-16x16.png" sizes="16x16">
    <style>
        html {{
            box-sizing: border-box;
            overflow: -moz-scrollbars-vertical;
            overflow-y: scroll;
        }}
        *, *:before, *:after {{
            box-sizing: inherit;
        }}
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="/static/swagger-ui/dist/swagger-ui-bundle.js" charset="UTF-8"></script>
    <script src="/static/swagger-ui/dist/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
    <script>
        window.onload = function() {{
            const ui = SwaggerUIBundle({{
                url: "{openapi_url}",
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIStandalonePreset
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout"
            }})
            window.ui = ui
        }}
    </script>
</body>
</html>
""".format(title=settings.APP_NAME, openapi_url="/api/openapi.json"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Swagger UI文档加载失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档加载失败: {str(e)}"
        )


@app.get("/api/redoc", include_in_schema=False)
async def redoc_html():
    """
    自定义ReDoc文档页面
    
    使用本地静态文件提供ReDoc，避免依赖CDN
    提供友好的API文档阅读界面
    
    Returns:
        HTMLResponse: ReDoc HTML页面
    
    错误码：
    - 404: 静态文件不存在
    - 500: 文档加载失败
    """
    try:
        logger.debug("加载ReDoc文档")
        
        # 检查静态文件是否存在
        import os
        redoc_path = "static/redoc/redoc.standalone.js"
        if not os.path.exists(redoc_path):
            logger.error(f"ReDoc静态文件不存在: {redoc_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="ReDoc静态文件不存在，请确保已正确安装"
            )
        
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" type="image/png" href="/static/swagger-ui/favicon-32x32.png" sizes="32x32">
    <style>
        body {{
            margin: 0;
            padding: 0;
        }}
    </style>
</head>
<body>
    <redoc spec-url="{openapi_url}"></redoc>
    <script src="/static/redoc/redoc.standalone.js"></script>
</body>
</html>
""".format(title=settings.APP_NAME, openapi_url="/api/openapi.json"))
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"ReDoc文档加载失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文档加载失败: {str(e)}"
        )


# ==================== 应用启动 ====================

if __name__ == "__main__":
    """
    直接运行此文件时启动应用
    
    使用uvicorn ASGI服务器运行FastAPI应用
    开发环境启用自动重载功能
    """
    import uvicorn
    
    logger.info("="*80)
    logger.info("准备启动Uvicorn服务器...")
    logger.info(f"  - 主机: {settings.HOST}")
    logger.info(f"  - 端口: {settings.PORT}")
    logger.info(f"  - 重载: {settings.DEBUG}")
    logger.info("="*80)
    
    # 启动uvicorn服务器
    uvicorn.run(
        "main:app",                    # 应用路径
        host=settings.HOST,            # 监听地址（0.0.0.0表示所有网卡）
        port=settings.PORT,            # 监听端口
        reload=settings.DEBUG          # 是否启用自动重载（开发环境）
    )
