/**
 * 数据集相关 API 服务
 * 提供数据集列表、结构查询等接口
 */

import { get } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/constants';
import type { DatasetListResponse, DatasetSchemaResponse } from '@/types';

/**
 * 获取所有数据集列表
 */
export const getDatasetList = async (): Promise<DatasetListResponse> => {
  return get<DatasetListResponse>(API_ENDPOINTS.EXPERIMENTAL.DATASETS);
};

/**
 * 获取数据集结构信息
 */
export const getDatasetSchema = async (datasetId: string): Promise<DatasetSchemaResponse> => {
  return get<DatasetSchemaResponse>(API_ENDPOINTS.EXPERIMENTAL.DATASET_SCHEMA(datasetId));
};
