/**
 * 覆盖率统计 API 服务
 * 提供数据集覆盖率查询功能
 */

import { get } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/constants';
import type { CoverageResponse, AllCoverageResponse } from '@/types';

/**
 * 获取单个数据集的覆盖率统计
 */
export const getDatasetCoverage = async (datasetId: string): Promise<CoverageResponse> => {
  return get<CoverageResponse>(API_ENDPOINTS.EXPERIMENTAL.COVERAGE(datasetId));
};

/**
 * 获取所有数据集的覆盖率汇总
 */
export const getAllCoverage = async (): Promise<AllCoverageResponse> => {
  return get<AllCoverageResponse>(API_ENDPOINTS.EXPERIMENTAL.ALL_COVERAGE);
};
