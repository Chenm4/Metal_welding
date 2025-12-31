/**
 * 类型定义文件
 * 定义整个应用中使用的 TypeScript 类型接口
 */

// ==================== 用户相关类型 ====================

/**
 * 用户角色类型
 */
export type UserRole = 'root' | 'admin' | 'user';

/**
 * 用户信息接口
 */
export interface User {
  id: number;
  username: string;
  role: UserRole;
  created_at?: string;
}

/**
 * 登录请求参数
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * 登录响应数据
 */
export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// ==================== 数据集相关类型 ====================

/**
 * 数据集信息
 */
export interface Dataset {
  id: string;
  display_name: string;
  table_name: string;
  description?: string;
}

/**
 * 数据集列表响应
 */
export interface DatasetListResponse {
  datasets: Dataset[];
  total: number;
}

/**
 * 字段分类类型
 */
export type FieldCategory = '物性' | '工艺' | '状态' | '性能' | '其他';

/**
 * 字段定义
 */
export interface Field {
  name: string;
  display_name: string;
  type: string;
  category: string; // 使用 string 以兼容后端返回的分类
  required: boolean;
  searchable: boolean;
  unit?: string;
  description?: string;
}

/**
 * 数据集结构响应
 */
export interface DatasetSchemaResponse {
  dataset_id: string;
  display_name: string;
  table_name: string;
  fields: Field[];
  categories: {
    [key: string]: Field[];
  };
  searchable_fields: string[];
  required_fields: string[];
  total_fields: number;
}

// ==================== 实验数据相关类型 ====================

/**
 * 实验数据记录（动态字段）
 */
export interface ExperimentalData {
  id: number;
  created_at?: string;
  updated_at?: string;
  created_by?: string;
  updated_by?: string;
  [key: string]: any; // 动态字段
}

/**
 * 分页查询参数
 */
export interface PaginationParams {
  page: number;
  page_size: number;
}

/**
 * 数据列表响应
 */
export interface DataListResponse {
  data: ExperimentalData[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * 搜索响应（继承数据列表响应）
 */
export interface SearchResponse extends DataListResponse {
  keyword: string;
}

/**
 * 数据创建/更新请求
 */
export interface DataMutationRequest {
  [key: string]: any;
}

/**
 * 数据操作响应
 */
export interface DataMutationResponse {
  message: string;
  data_id?: number;
  deleted_count?: number;
}

/**
 * 批量导入响应
 */
export interface BatchImportResponse {
  message: string;
  dataset_id: string;
  filename: string;
  total: number;
  success: number;
  duplicates: number;
  failed: number;
  dataset_created?: boolean;
  table_name?: string;
  fields_count?: number;
  creation_message?: string;
}

// ==================== 覆盖率统计相关类型 ====================

/**
 * 覆盖率分布
 */
export interface CoverageDistribution {
  [range: string]: number;
}

/**
 * 低覆盖率记录
 */
export interface LowCoverageRecord {
  id: number;
  identifier: string;
  coverage: number;
  full_data?: Record<string, any>;
  missing_fields?: string[];
}

/**
 * 字段覆盖率
 */
export interface FieldCoverage {
  [field: string]: number;
}

/**
 * 覆盖率统计响应
 */
export interface CoverageResponse {
  comprehensive_coverage: number;
  average_coverage: number;
  coverage_distribution: CoverageDistribution;
  low_coverage_records: LowCoverageRecord[];
  field_coverage: FieldCoverage;
  meets_threshold: boolean;
  threshold: number;
  message?: string;
  warning?: string;
}

/**
 * 所有数据集覆盖率汇总
 */
export interface AllCoverageResponse {
  overall_coverage: number;
  total_records: number;
  total_datasets: number;
  meets_threshold: boolean;
  message?: string;
  warning?: string;
  datasets: Array<{
    dataset_id: string;
    display_name: string;
    total_records: number;
    comprehensive_coverage: number;
    average_coverage: number;
    meets_threshold: boolean;
    [key: string]: any;
  }>;
}

// ==================== API 响应类型 ====================

/**
 * 通用 API 错误响应
 */
export interface ApiError {
  detail: string;
}

/**
 * 通用成功响应
 */
export interface SuccessResponse {
  message: string;
}
