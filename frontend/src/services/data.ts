/**
 * 实验数据相关 API 服务
 * 提供数据的 CRUD 操作、搜索、导入等功能
 */

import { get, post, put, del, upload } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/constants';
import type {
  DataListResponse,
  SearchResponse,
  ExperimentalData,
  DataMutationRequest,
  DataMutationResponse,
  BatchImportResponse,
  PaginationParams,
} from '@/types';

/**
 * 获取数据列表（分页）
 */
export const getDataList = async (
  datasetId: string,
  params: PaginationParams
): Promise<DataListResponse> => {
  return get<DataListResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_LIST(datasetId), { params });
};

/**
 * 搜索数据
 */
export const searchData = async (
  datasetId: string,
  keyword: string,
  params: PaginationParams
): Promise<SearchResponse> => {
  return get<SearchResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_SEARCH(datasetId), {
    params: {
      ...params,
      keyword,
    },
  });
};

/**
 * 获取单条数据详情
 */
export const getDataDetail = async (
  datasetId: string,
  dataId: number
): Promise<ExperimentalData> => {
  return get<ExperimentalData>(API_ENDPOINTS.EXPERIMENTAL.DATA_DETAIL(datasetId, dataId));
};

/**
 * 创建数据
 */
export const createData = async (
  datasetId: string,
  data: DataMutationRequest
): Promise<DataMutationResponse> => {
  return post<DataMutationResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_CREATE(datasetId), data);
};

/**
 * 更新数据
 */
export const updateData = async (
  datasetId: string,
  dataId: number,
  data: DataMutationRequest
): Promise<DataMutationResponse> => {
  return put<DataMutationResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_UPDATE(datasetId, dataId), data);
};

/**
 * 删除单条数据
 */
export const deleteData = async (
  datasetId: string,
  dataId: number
): Promise<DataMutationResponse> => {
  return del<DataMutationResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_DELETE(datasetId, dataId));
};

/**
 * 批量删除数据
 */
export const batchDeleteData = async (
  datasetId: string,
  dataIds: number[]
): Promise<DataMutationResponse> => {
  return post<DataMutationResponse>(API_ENDPOINTS.EXPERIMENTAL.BATCH_DELETE(datasetId), dataIds);
};

/**
 * 导入 CSV/Excel 文件
 */
export const importFile = async (
  datasetId: string,
  file: File
): Promise<BatchImportResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  return upload<BatchImportResponse>(API_ENDPOINTS.EXPERIMENTAL.DATA_IMPORT(datasetId), formData);
};
