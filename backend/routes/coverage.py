"""数据覆盖率统计路由"""
from fastapi import APIRouter, HTTPException, Depends, status
from backend.services.coverage_service import CoverageService
from backend.routes.auth import get_current_user
from backend.utils.logger import get_logger


router = APIRouter(prefix="/api/coverage", tags=["数据覆盖率"])
coverage_service = CoverageService()
logger = get_logger(__name__)


@router.get("/batches/{batch_id}", summary="获取指定批次的覆盖率统计")
async def get_batch_coverage(
    batch_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定批次的数据覆盖率统计
    
    - **batch_id**: 批次ID (1-4)
    
    返回内容:
    - 综合覆盖率: 整个批次所有数据项的填充率
    - 平均覆盖率: 所有记录覆盖率的平均值
    - 覆盖率分布: 不同覆盖率区间的记录数量
    - 低覆盖率记录: 覆盖率低于阈值(90%)的记录列表
    - 字段覆盖率: 每个字段的填充率
    - 达标提示: 是否达到90%阈值要求
    
    错误码：
    - 400: 批次ID无效
    - 401: Token无效
    - 500: 计算失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求批次{batch_id}的覆盖率统计")
        
        result = coverage_service.calculate_batch_coverage(batch_id)
        
        # 添加提示信息
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 数据覆盖率未达到90%阈值！当前覆盖率: {result['comprehensive_coverage']}%"
            logger.warning(f"批次{batch_id}覆盖率未达标: {result['comprehensive_coverage']}%")
        else:
            result["message"] = f"✓ 数据覆盖率达标！当前覆盖率: {result['comprehensive_coverage']}%"
            logger.info(f"✓ 批次{batch_id}覆盖率达标: {result['comprehensive_coverage']}%")
        
        return result
    
    except ValueError as e:
        logger.warning(f"批次ID无效: {batch_id}, 错误: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 批次{batch_id}覆盖率计算失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"覆盖率计算失败: {str(e)}"
        )


@router.get("/all", summary="获取所有批次的覆盖率汇总")
async def get_all_batches_coverage(
    current_user: dict = Depends(get_current_user)
):
    """
    获取所有批次的数据覆盖率汇总统计
    
    返回内容:
    - 总体覆盖率: 所有批次综合计算的覆盖率
    - 各批次统计: 每个批次的详细覆盖率信息
    - 是否达标: 是否满足90%的阈值要求
    - 达标提示: 明确显示是否达到要求
    
    错误码：
    - 401: Token无效
    - 500: 计算失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求所有批次的覆盖率汇总")
        
        result = coverage_service.calculate_all_batches_coverage()
        
        # 添加提示信息
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 总体数据覆盖率未达到90%阈值！当前总体覆盖率: {result['overall_coverage']}%"
            logger.warning(f"总体覆盖率未达标: {result['overall_coverage']}%")
        else:
            result["message"] = f"✓ 总体数据覆盖率达标！当前总体覆盖率: {result['overall_coverage']}%"
            logger.info(f"✓ 总体覆盖率达标: {result['overall_coverage']}%")
        
        return result
    
    except Exception as e:
        logger.error(f"✗ 覆盖率汇总计算失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"覆盖率汇总计算失败: {str(e)}"
        )
