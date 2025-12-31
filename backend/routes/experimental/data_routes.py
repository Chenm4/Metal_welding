"""实验数据统一路由 - 支持所有数据集"""
from fastapi import APIRouter, HTTPException, Depends, Query, status, UploadFile, File
from typing import List, Optional, Dict, Any
import pandas as pd
import io

from backend.models.experimental.metadata import DatasetMetadata
from backend.models.experimental.schemas import (
    DataResponse, DataCreateResponse, DataUpdateResponse, DataDeleteResponse,
    BatchImportResponse, DatasetSchemaResponse, DatasetListResponse
)
from backend.services.experimental.base_service import BaseExperimentalDataService
from backend.services.experimental.coverage_service import CoverageService, calculate_all_datasets_coverage
from backend.services.experimental.dataset_creator import DatasetCreator
from backend.routes.auth import get_current_user, require_admin
from backend.utils.logger import get_logger


router = APIRouter(prefix="/api/experimental-data", tags=["实验数据"])
logger = get_logger(__name__)


# ========== 覆盖率统计（必须在/{dataset_id}之前）==========

@router.get("/coverage/all", summary="获取所有数据集的覆盖率汇总")
async def get_all_coverage(current_user: dict = Depends(get_current_user)):
    """
    获取所有数据集的覆盖率汇总统计
    
    错误码：
    - 401: Token无效
    - 500: 计算失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求所有数据集覆盖率汇总")
        result = calculate_all_datasets_coverage()
        
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 总体数据覆盖率未达到90%阈值！当前总体覆盖率: {result['overall_coverage']}%"
            logger.warning(f"总体数据集覆盖率未达标: {result['overall_coverage']}%")
        else:
            result["message"] = f"✓ 总体数据覆盖率达标！当前总体覆盖率: {result['overall_coverage']}%"
            logger.info(f"✓ 总体数据集覆盖率达标: {result['overall_coverage']}%")
        
        return result
    except Exception as e:
        logger.error(f"✗ 覆盖率汇总计算失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"覆盖率汇总计算失败: {str(e)}"
        )


# ========== 覆盖率统计 ==========

@router.get("/{dataset_id}/coverage", summary="获取指定数据集的覆盖率")
async def get_dataset_coverage(
    dataset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定数据集的覆盖率统计
    
    - **dataset_id**: 数据集ID
    
    错误码：
    - 401: Token无效
    - 404: 数据集不存在
    - 500: 计算失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求数据集 '{dataset_id}' 的覆盖率")
        coverage_service = CoverageService(dataset_id)
        result = coverage_service.calculate_batch_coverage()
        
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 数据集覆盖率未达到90%阈值！当前覆盖率: {result['comprehensive_coverage']}%"
            logger.warning(f"数据集 '{dataset_id}' 覆盖率未达标: {result['comprehensive_coverage']}%")
        else:
            result["message"] = f"✓ 数据集覆盖率达标！当前覆盖率: {result['comprehensive_coverage']}%"
            logger.info(f"✓ 数据集 '{dataset_id}' 覆盖率达标: {result['comprehensive_coverage']}%")
        
        return result
    except ValueError as e:
        logger.warning(f"数据集不存在: {dataset_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 获取数据集 '{dataset_id}' 覆盖率失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据集覆盖率失败: {str(e)}"
        )


# ========== 数据集管理 ==========

@router.get("/datasets", response_model=DatasetListResponse, summary="列出所有数据集")
async def list_datasets(current_user: dict = Depends(get_current_user)):
    """
    获取所有可用的数据集列表
    
    返回每个数据集的ID、名称、表名和描述信息
    
    错误码：
    - 401: Token无效
    - 500: 获取失败
    """
    try:
        logger.debug(f"用户 {current_user['username']} 请求数据集列表")
        datasets = DatasetMetadata.list_all_datasets()
        logger.debug(f"找到 {len(datasets)} 个数据集")
        return {
            "datasets": datasets,
            "total": len(datasets)
        }
    except Exception as e:
        logger.error(f"✗ 获取数据集列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据集列表失败: {str(e)}"
        )


@router.get("/{dataset_id}/schema", response_model=DatasetSchemaResponse, summary="获取数据集结构")
async def get_dataset_schema(
    dataset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定数据集的字段结构（用于前端动态渲染表格）
    
    - **dataset_id**: 数据集ID，如 '1', '1'
    
    返回:
    - 所有字段列表
    - 按分类（物性/工艺/状态/性能）分组的字段
    - 可搜索字段列表
    - 必填字段列表
    
    错误码：
    - 401: Token无效
    - 404: 数据集不存在
    - 500: 获取失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 请求数据集 '{dataset_id}' 的结构")
        metadata = DatasetMetadata(dataset_id)
        
        result = {
            "dataset_id": dataset_id,
            "display_name": metadata.get_display_name(),
            "table_name": metadata.get_table_name(),
            "fields": metadata.get_data_fields(),
            "categories": metadata.get_all_categories(),
            "searchable_fields": metadata.get_searchable_fields(),
            "required_fields": metadata.get_required_fields(),
            "total_fields": len(metadata.get_all_field_names())
        }
        logger.debug(f"数据集 '{dataset_id}' 结构: {result['total_fields']} 个字段")
        return result
        
    except ValueError as e:
        logger.warning(f"数据集不存在: {dataset_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 获取数据集结构失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取数据集结构失败: {str(e)}"
        )


# ========== 数据查询 ==========

@router.get("/{dataset_id}/search", summary="搜索数据")
async def search_data(
    dataset_id: str,
    keyword: str = Query(..., min_length=1, description="搜索关键词"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    在指定数据集中进行关键词搜索
    
    自动在可搜索字段中查找（可搜索字段从元数据配置获取）
    
    错误码：
    - 401: Token无效
    - 404: 数据集不存在
    - 500: 搜索失败
    """
    try:
        logger.info(f"用户 {current_user['username']} 在数据集 '{dataset_id}' 中搜索: '{keyword}'")
        
        service = BaseExperimentalDataService(dataset_id)
        data_list, total = service.search(keyword, page, page_size)
        
        logger.info(f"搜索到 {total} 条结果，返回第 {page} 页 ({len(data_list)} 条)")
        
        return {
            "data": data_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
            "keyword": keyword
        }
    except ValueError as e:
        logger.warning(f"数据集不存在: {dataset_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 搜索失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/{dataset_id}", summary="获取数据列表")
async def list_data(
    dataset_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: dict = Depends(get_current_user)
):
    """
    分页查询指定数据集的数据
    
    - **dataset_id**: 数据集ID
    - **page**: 页码
    - **page_size**: 每页数量
    
    错误码：
    - 401: Token无效
    - 404: 数据集不存在
    - 500: 查询失败
    """
    try:
        logger.debug(f"用户 {current_user['username']} 查询数据集 '{dataset_id}': page={page}, page_size={page_size}")
        
        service = BaseExperimentalDataService(dataset_id)
        data_list, total = service.list_data(page, page_size, filters=None)
        
        logger.debug(f"查询到 {len(data_list)} 条数据，总数: {total}")
        
        return {
            "data": data_list,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    except ValueError as e:
        logger.warning(f"数据集不存在: {dataset_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 查询失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


# ========== 单条数据的CRUD操作 ==========

@router.get("/{dataset_id}/{data_id}", summary="获取单条数据")
async def get_data_by_id(
    dataset_id: str,
    data_id: int,
    current_user: dict = Depends(get_current_user)
):
    """
    根据ID获取单条实验数据
    
    - **dataset_id**: 数据集ID（如 1, 2
    - **data_id**: 数据记录ID
    
    错误码：
    - 401: Token无效
    - 404: 数据不存在
    - 500: 查询失败
    """
    try:
        logger.debug(f"用户 {current_user['username']} 请求数据: dataset={dataset_id}, id={data_id}")
        
        service = BaseExperimentalDataService(dataset_id)
        data = service.get_by_id(data_id)
        
        if not data:
            logger.warning(f"数据不存在: dataset={dataset_id}, id={data_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        logger.debug(f"✓ 获取数据成功: id={data_id}")
        return data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 查询失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.post("/{dataset_id}/data", summary="创建单条数据")
async def create_data(
    dataset_id: str,
    data: Dict[str, Any],
    current_user: dict = Depends(require_admin)
):
    """
    创建新的实验数据（仅管理员）
    
    - **dataset_id**: 数据集ID（如 1, 2
    - **data**: 实验数据（JSON对象）
    
    错误码：
    - 400: 数据验证失败
    - 401: Token无效
    - 403: 非管理员权限
    - 500: 创建失败
    """
    try:
        logger.info(f"管理员 {current_user['username']} 创建数据: dataset={dataset_id}")
        logger.debug(f"数据字段: {list(data.keys())}")
        
        service = BaseExperimentalDataService(dataset_id)
        data_id = service.create(
            data=data,
            created_by=current_user['username']
        )
        
        logger.info(f"✓ 数据创建成功: id={data_id}")
        return {
            "message": "数据创建成功",
            "data_id": data_id
        }
        
    except ValueError as e:
        logger.warning(f"数据验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"✗ 创建失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建失败: {str(e)}"
        )


@router.put("/{dataset_id}/{data_id}", summary="更新单条数据")
async def update_data(
    dataset_id: str,
    data_id: int,
    data: Dict[str, Any],
    current_user: dict = Depends(require_admin)
):
    """
    更新实验数据（仅管理员）
    
    - **dataset_id**: 数据集ID（如 1, 2
    - **data_id**: 数据记录ID
    - **data**: 更新的字段（JSON对象）
    
    错误码：
    - 400: 没有提供更新字段
    - 401: Token无效
    - 403: 非管理员权限
    - 404: 数据不存在
    - 500: 更新失败
    """
    try:
        if not data:
            logger.warning("更新失败: 没有提供更新字段")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供更新字段"
            )
        
        logger.info(f"管理员 {current_user['username']} 更新数据: dataset={dataset_id}, id={data_id}")
        logger.debug(f"更新字段: {list(data.keys())}")
        
        service = BaseExperimentalDataService(dataset_id)
        success = service.update(
            data_id=data_id,
            data=data,
            updated_by=current_user['username']
        )
        
        if not success:
            logger.warning(f"数据不存在: dataset={dataset_id}, id={data_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        logger.info(f"✓ 数据更新成功: id={data_id}")
        return {"message": "数据更新成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 更新失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新失败: {str(e)}"
        )


@router.delete("/{dataset_id}/{data_id}", summary="删除单条数据")
async def delete_data(
    dataset_id: str,
    data_id: int,
    current_user: dict = Depends(require_admin)
):
    """
    删除实验数据（仅管理员）
    
    - **dataset_id**: 数据集ID（如 1, 2）
    - **data_id**: 数据记录ID
    
    错误码：
    - 401: Token无效
    - 403: 非管理员权限
    - 404: 数据不存在
    - 500: 删除失败
    """
    try:
        logger.info(f"管理员 {current_user['username']} 删除数据: dataset={dataset_id}, id={data_id}")
        
        service = BaseExperimentalDataService(dataset_id)
        success = service.delete(data_id)
        
        if not success:
            logger.warning(f"数据不存在: dataset={dataset_id}, id={data_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="数据不存在"
            )
        
        logger.info(f"✓ 数据删除成功: id={data_id}")
        return {"message": "数据删除成功"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 删除失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.post("/{dataset_id}/batch-delete", summary="批量删除数据")
async def batch_delete_data(
    dataset_id: str,
    data_ids: List[int],
    current_user: dict = Depends(require_admin)
):
    """
    批量删除数据（仅管理员）
    
    错误码：
    - 400: ID列表为空
    - 401: Token无效
    - 403: 非管理员权限
    - 500: 删除失败
    """
    try:
        if not data_ids:
            logger.warning("批量删除失败: 数据ID列表为空")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="数据ID列表不能为空"
            )
        
        logger.info(f"管理员 {current_user['username']} 批量删除数据: dataset={dataset_id}, count={len(data_ids)}")
        
        service = BaseExperimentalDataService(dataset_id)
        deleted_count = service.batch_delete(data_ids)
        
        logger.info(f"✓ 批量删除成功: {deleted_count} 条")
        return {
            "message": f"成功删除 {deleted_count} 条数据",
            "deleted_count": deleted_count
        }
        
    except ValueError as e:
        logger.warning(f"批量删除失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"✗ 批量删除失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量删除失败: {str(e)}"
        )


# ========== 数据导入 ==========

@router.post("/{dataset_id}/import", response_model=BatchImportResponse, summary="导入CSV/Excel文件（支持新数据集自动创建）")
async def import_file(
    dataset_id: str,
    file: UploadFile = File(..., description="CSV或Excel文件"),
    current_user: dict = Depends(require_admin)
):
    """
    批量导入CSV或Excel文件（仅管理员）
    
    **智能特性**:
    - ✅ **自动创建新数据集**: 上传 batch_5 时自动创建表和配置，无需预先存在
    - ✅ 支持CSV和Excel格式（.csv, .xlsx）
    - ✅ 自动推断字段分类（物性/工艺/状态/性能）
    - ✅ 自动验证文件列名与数据库表结构一致性
    - ✅ 导入前检查重复数据，避免重复插入
    - ✅ 返回导入统计：成功、重复、失败数量
    
    **工作流程**:
    1. 检查数据集是否存在
    2. 如果不存在：读取CSV表头 → 创建数据库表 → 生成元数据配置
    3. 验证列名一致性
    4. 批量导入数据
    """
    try:
        # 验证文件类型
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        file_ext = file.filename.lower().split('.')[-1]
        if file_ext not in ['csv', 'xlsx', 'xls']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="仅支持CSV和Excel格式文件（.csv, .xlsx, .xls）"
            )
        
        # 读取文件内容
        contents = await file.read()
        
        # 根据文件类型解析
        try:
            if file_ext == 'csv':
                # 尝试不同编码
                try:
                    df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(io.BytesIO(contents), encoding='gbk')
                    except UnicodeDecodeError:
                        df = pd.read_csv(io.BytesIO(contents), encoding='gb2312')
            else:
                df = pd.read_excel(io.BytesIO(contents))
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件解析失败: {str(e)}"
            )
        
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件为空，没有数据"
            )
        
        # 获取CSV列名
        file_columns = df.columns.tolist()
        
        # 检查数据集是否存在
        creator = DatasetCreator()
        metadata_exists, table_exists = creator.check_dataset_exists(dataset_id)
        
        dataset_created = False
        creation_info = None
        
        # 如果数据集不存在，自动创建
        if not metadata_exists or not table_exists:
            creation_info = creator.create_new_dataset(dataset_id, file_columns)
            dataset_created = creation_info.get("created", False)
            
            if not creation_info.get("created", False) and not (metadata_exists and table_exists):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"数据集创建失败: {creation_info.get('message', '未知错误')}"
                )
            
            # 强制重新加载元数据缓存
            DatasetMetadata.reload_metadata()
        
        # 重新加载元数据（如果是新创建的）
        try:
            metadata = DatasetMetadata(dataset_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"数据集 '{dataset_id}' 不存在且创建失败: {str(e)}"
            )
        
        # 验证列名（对于新创建的数据集，应该完全匹配）
        valid, error_msg = metadata.validate_import_columns(file_columns)
        
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # 将 NaN 替换为 None（MySQL 的 NULL）
        df = df.replace({pd.NA: None, float('nan'): None})
        df = df.where(pd.notna(df), None)
        
        # 转换DataFrame为字典列表
        data_list = df.to_dict('records')
        
        # 批量导入
        service = BaseExperimentalDataService(dataset_id)
        import_result = service.batch_import(
            data_list=data_list,
            created_by=current_user['username']
        )
        
        # 构建响应
        response = {
            "message": "导入完成",
            "dataset_id": dataset_id,
            "filename": file.filename,
            **import_result
        }
        
        # 如果是新创建的数据集，添加创建信息
        if dataset_created and creation_info:
            response["dataset_created"] = True
            response["table_name"] = creation_info.get("table_name")
            response["fields_count"] = creation_info.get("fields_count")
            response["creation_message"] = f"✨ 新数据集 '{dataset_id}' 已自动创建！表名: {creation_info.get('table_name')}, 字段数: {creation_info.get('fields_count')}"
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"导入失败: {str(e)}"
        )


# ========== 覆盖率统计 ==========

@router.get("/{dataset_id}/coverage", summary="获取数据集覆盖率统计")
async def get_dataset_coverage(
    dataset_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    获取指定数据集的覆盖率统计
    
    - 综合覆盖率: 整个数据集所有数据项的填充率
    - 平均覆盖率: 所有记录覆盖率的平均值
    - 覆盖率分布: 不同覆盖率区间的记录数量
    - 低覆盖率记录: 覆盖率低于阈值的记录列表
    - 字段覆盖率: 每个字段的填充率
    - 达标提示: 是否达到阈值要求
    """
    try:
        coverage_service = CoverageService(dataset_id)
        result = coverage_service.calculate_batch_coverage()
        
        # 添加提示信息
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 数据覆盖率未达到{result['threshold']}%阈值！当前覆盖率: {result['comprehensive_coverage']}%"
        else:
            result["message"] = f"✓ 数据覆盖率达标！当前覆盖率: {result['comprehensive_coverage']}%"
        
        return result
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"覆盖率计算失败: {str(e)}"
        )


@router.get("/coverage/all", summary="获取所有数据集的覆盖率汇总")
async def get_all_coverage(current_user: dict = Depends(get_current_user)):
    """
    获取所有数据集的覆盖率汇总统计
    
    返回:
    - 总体覆盖率: 所有数据集综合计算的覆盖率
    - 各数据集统计: 每个数据集的详细覆盖率信息
    - 是否达标: 是否满足阈值要求
    """
    try:
        result = calculate_all_datasets_coverage()
        
        # 添加提示信息
        if not result["meets_threshold"]:
            result["warning"] = f"⚠️ 总体数据覆盖率未达到90%阈值！当前总体覆盖率: {result['overall_coverage']}%"
        else:
            result["message"] = f"✓ 总体数据覆盖率达标！当前总体覆盖率: {result['overall_coverage']}%"
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"覆盖率汇总计算失败: {str(e)}"
        )
