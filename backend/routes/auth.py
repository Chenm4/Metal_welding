"""
认证相关路由

提供用户认证和管理相关的API端点：
1. 用户登录（获取JWT Token）
2. 获取当前用户信息
3. 创建用户（管理员权限）
4. 获取用户列表（管理员权限）
5. 更新用户信息（管理员权限）
6. 删除用户（管理员权限）

"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.models.user import UserLogin, TokenResponse, UserCreate, UserResponse, UserUpdate
from backend.services.auth_service import AuthService
from backend.utils.logger import get_logger

# ==================== 初始化 ====================
# 创建路由器 - prefix定义所有端点的前缀路径
router = APIRouter(prefix="/api/auth", tags=["认证"])

# HTTP Bearer认证方案 - 用于提取Authorization header中的token
security = HTTPBearer()

# 认证服务实例 - 处理用户认证和管理的业务逻辑
auth_service = AuthService()

# 日志记录器
logger = get_logger(__name__)


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    获取当前用户（依赖注入）
    
    从HTTP Authorization header中提取JWT Token，验证并返回用户信息
    用于需要登录才能访问的API端点
    
    Args:
        credentials: HTTP Bearer认证凭据，由FastAPI自动注入
    
    Returns:
        dict: 用户信息字典，包含id、username、role等字段
    
    Raises:
        HTTPException(401): Token无效或用户不存在
    
    使用示例：
        @router.get("/protected")
        async def protected_route(current_user: dict = Depends(get_current_user)):
            return {"user": current_user["username"]}
    """
    # 提取Token字符串
    token = credentials.credentials
    logger.debug(f"验证Token: {token[:20]}...")
    
    # 验证Token并解码
    payload = auth_service.verify_token(token)
    
    if not payload:
        logger.warning(f"Token验证失败: 无效的认证凭据")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据"
        )
    
    # 从payload中提取用户名并查询用户信息
    username = payload.get('sub')
    logger.debug(f"Token验证成功，用户名: {username}")
    
    user = auth_service.get_user_by_username(username)
    if not user:
        logger.warning(f"用户不存在: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )
    
    logger.debug(f"用户身份验证成功: {username} (角色: {user.get('role')})")
    return user


def require_root(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求超级管理员权限（依赖注入）
    
    检查当前用户是否具有root角色
    用于只允许超级管理员访问的API端点
    
    Args:
        current_user: 当前登录用户信息，由get_current_user依赖注入
    
    Returns:
        dict: 用户信息字典（如果是超级管理员）
    
    Raises:
        HTTPException(403): 用户不是超级管理员
    """
    username = current_user.get('username')
    role = current_user.get('role')
    
    logger.debug(f"权限检查: 用户 {username}, 角色 {role}")
    
    if role != 'root':
        logger.warning(f"权限不足: 用户 {username} (角色: {role}) 尝试访问超级管理员功能")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    
    logger.debug(f"权限验证通过: 用户 {username} 是超级管理员")
    return current_user


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """
    要求管理员权限（依赖注入）
    
    检查当前用户是否具有管理员或超级管理员角色
    用于允许管理员和超级管理员访问的API端点
    
    Args:
        current_user: 当前登录用户信息，由get_current_user依赖注入
    
    Returns:
        dict: 用户信息字典（如果是管理员或超级管理员）
    
    Raises:
        HTTPException(403): 用户不是管理员
    
    使用示例：
        @router.post("/admin-only")
        async def admin_route(current_user: dict = Depends(require_admin)):
            return {"message": "管理员专属功能"}
    """
    # 检查用户角色
    username = current_user.get('username')
    role = current_user.get('role')
    
    logger.debug(f"权限检查: 用户 {username}, 角色 {role}")
    
    if role not in ['admin', 'root']:
        logger.warning(f"权限不足: 用户 {username} (角色: {role}) 尝试访问管理员功能")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    logger.debug(f"权限验证通过: 用户 {username} 是管理员或超级管理员")
    return current_user


# ==================== API端点 ====================

@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(credentials: UserLogin):
    """
    用户登录接口
    
    验证用户名和密码，成功后返回JWT Token和用户信息
    Token默认有效期30分钟，需在后续请求中放入Authorization header
    
    请求体：
    - **username**: 用户名（必填）
    - **password**: 密码（必填）
    
    返回：
    - **access_token**: JWT Token字符串
    - **token_type**: Token类型（固定为"bearer"）
    - **user**: 用户信息（id、username、role、status等）
    
    错误码：
    - 401: 用户名或密码错误
    - 500: 服务器内部错误
    
    使用示例：
    ```bash
    curl -X POST "http://localhost:8000/api/auth/login" \\
      -H "Content-Type: application/json" \\
      -d '{"username": "admin", "password": "123456"}'
    ```
    """
    logger.info(f"收到登录请求: username={credentials.username}")
    
    try:
        # 调用认证服务验证用户名和密码
        user = auth_service.authenticate(credentials.username, credentials.password)
        
        if not user:
            logger.warning(f"登录失败: 用户名或密码错误 - username={credentials.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误"
            )
        
        logger.info(f"用户认证成功: {credentials.username} (角色: {user.get('role')})")
        
        # 生成JWT Token
        logger.debug(f"正在生成Token: username={credentials.username}")
        token = auth_service.create_access_token(user)
        logger.info(f"Token生成成功: username={credentials.username}")
        
        # 构造响应 - 使用Pydantic模型确保数据结构正确
        logger.info(f"✓ 用户登录成功: {credentials.username}")
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserResponse(**user)
        )
        
    except HTTPException:
        # 重新抛出HTTP异常（已经被记录）
        raise
    except Exception as e:
        # 记录未预期的异常
        logger.error(
            f"✗ 登录过程发生异常: username={credentials.username}, "
            f"异常类型={type(e).__name__}, 异常信息={str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录失败，请稍后重试"
        )


@router.options("/login", summary="预检请求处理")
async def options_login() -> Response:
    """
    处理浏览器对 /api/auth/login 的 CORS 预检请求（OPTIONS）。
    返回 204，由 CORSMiddleware 自动附带 CORS 响应头。
    """
    return Response(status_code=204)


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """
    获取当前登录用户的信息
    
    错误码：
    - 401: Token无效或已过期
    - 500: 服务器内部错误
    """
    try:
        return UserResponse(**current_user)
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户信息失败: {str(e)}"
        )


@router.post("/users", response_model=dict, summary="创建用户", dependencies=[Depends(require_admin)])
async def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
    """
    创建新用户（管理员或超级管理员）
    
    权限规则：
    - root 可以创建所有角色的用户（root、admin、user）
    - admin 只能创建普通用户（user）
    
    - **username**: 用户名（3-50字符）
    - **password**: 密码（6-100字符）
    - **role**: 角色（root/admin/user）
    
    错误码：
    - 400: 用户名已存在、参数验证失败
    - 401: Token无效
    - 403: 权限不足
    - 500: 创建失败
    """
    try:
        current_role = current_user['role']
        target_role = user.role
        
        # 权限检查：admin 只能创建 user
        if current_role == 'admin' and target_role != 'user':
            logger.warning(f"权限不足: 管理员 {current_user['username']} 尝试创建 {target_role} 角色")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员只能创建普通用户"
            )
        
        logger.info(f"{current_role} {current_user['username']} 尝试创建用户: {user.username} (角色: {target_role})")
        
        # 检查用户名是否已存在
        existing_user = auth_service.get_user_by_username(user.username)
        if existing_user:
            logger.warning(f"用户名已存在: {user.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用户名已存在"
            )
        
        user_id = auth_service.create_user(
            username=user.username,
            password=user.password,
            role=user.role,
            created_by=current_user['username']
        )
        
        logger.info(f"✓ 用户创建成功: {user.username} (ID: {user_id})")
        return {"message": "用户创建成功", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 用户创建失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"用户创建失败: {str(e)}"
        )


@router.get("/users", summary="获取用户列表", dependencies=[Depends(require_admin)])
async def list_users(
    page: int = 1,
    page_size: int = 20,
    current_user: dict = Depends(require_admin)
):
    """
    获取用户列表（仅管理员）
    
    - **page**: 页码
    - **page_size**: 每页数量
    
    错误码：
    - 400: 分页参数无效
    - 401: Token无效
    - 403: 非管理员权限
    - 500: 查询失败
    """
    try:
        logger.debug(f"管理员 {current_user['username']} 查询用户列表: page={page}, page_size={page_size}")
        
        # 验证分页参数
        if page < 1 or page_size < 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="页码和每页数量必须大于0"
            )
        if page_size > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="每页数量不能超过100"
            )
        
        users, total = auth_service.list_users(page, page_size)
        
        logger.debug(f"查询到 {len(users)} 个用户，总数: {total}")
        
        return {
            "data": [UserResponse(**u) for u in users],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 获取用户列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取用户列表失败: {str(e)}"
        )


@router.put("/users/{user_id}", response_model=dict, summary="更新用户", dependencies=[Depends(require_admin)])
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: dict = Depends(require_admin)
):
    """
    更新用户信息（仅管理员）
    
    - **user_id**: 用户ID
    - **password**: 新密码（可选）
    - **role**: 角色（可选）
    - **status**: 状态（可选）
    
    错误码：
    - 400: 没有提供更新字段、参数验证失败
    - 401: Token无效
    - 403: 非管理员权限
    - 404: 用户不存在
    - 500: 更新失败
    """
    try:
        logger.info(f"管理员 {current_user['username']} 尝试更新用户ID: {user_id}")
        
        updates = user_update.dict(exclude_unset=True)
        
        if not updates:
            logger.warning("更新用户失败: 没有提供更新字段")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供更新字段"
            )
        
        logger.debug(f"更新字段: {list(updates.keys())}")
        
        success = auth_service.update_user(user_id, **updates)
        
        if not success:
            logger.warning(f"用户不存在: ID={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"✓ 用户更新成功: ID={user_id}")
        return {"message": "用户更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 更新用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新用户失败: {str(e)}"
        )


@router.delete("/users/{user_id}", response_model=dict, summary="删除用户", dependencies=[Depends(require_admin)])
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    删除用户（管理员或超级管理员）
    
    权限规则：
    - root 可以删除 admin 和 user
    - admin 只能删除 user
    - 不能删除自己
    
    - **user_id**: 用户ID
    
    错误码：
    - 400: 不能删除自己
    - 401: Token无效
    - 403: 权限不足
    - 404: 用户不存在
    - 500: 删除失败
    """
    try:
        current_role = current_user['role']
        logger.info(f"{current_role} {current_user['username']} 尝试删除用户ID: {user_id}")
        
        # 不能删除自己
        if user_id == current_user['id']:
            logger.warning(f"用户尝试删除自己: {current_user['username']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="不能删除自己"
            )
        
        # 获取目标用户信息
        target_user = auth_service.get_user_by_id(user_id)
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        target_role = target_user.get('role')
        
        # 权限检查：admin 不能删除 admin 或 root
        if current_role == 'admin' and target_role in ['admin', 'root']:
            logger.warning(f"权限不足: 管理员 {current_user['username']} 尝试删除 {target_role}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理员只能删除普通用户"
            )
        
        success = auth_service.delete_user(user_id)
        
        if not success:
            logger.warning(f"用户不存在: ID={user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        logger.info(f"✓ 用户删除成功: ID={user_id}")
        return {"message": "用户删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 删除用户失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除用户失败: {str(e)}"
        )
