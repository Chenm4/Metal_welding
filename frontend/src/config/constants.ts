/**
 * 全局常量配置
 * 包含 API 地址、本地存储键、默认值等配置项
 */

// ==================== API 配置 ====================

/**
 * API 基础地址
 * 可通过环境变量覆盖
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8004';

/**
 * API 端点路径
 */
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/api/auth/login',
    CURRENT_USER: '/api/auth/me',
    USERS: '/api/auth/users',
  },
  
  // 实验数据相关
  EXPERIMENTAL: {
    DATASETS: '/api/experimental-data/datasets',
    DATASET_SCHEMA: (datasetId: string) => `/api/experimental-data/${datasetId}/schema`,
    DATA_LIST: (datasetId: string) => `/api/experimental-data/${datasetId}`,
    DATA_DETAIL: (datasetId: string, dataId: number) => `/api/experimental-data/${datasetId}/${dataId}`,
    DATA_CREATE: (datasetId: string) => `/api/experimental-data/${datasetId}/data`,
    DATA_UPDATE: (datasetId: string, dataId: number) => `/api/experimental-data/${datasetId}/${dataId}`,
    DATA_DELETE: (datasetId: string, dataId: number) => `/api/experimental-data/${datasetId}/${dataId}`,
    BATCH_DELETE: (datasetId: string) => `/api/experimental-data/${datasetId}/batch-delete`,
    DATA_SEARCH: (datasetId: string) => `/api/experimental-data/${datasetId}/search`,
    DATA_IMPORT: (datasetId: string) => `/api/experimental-data/${datasetId}/import`,
    COVERAGE: (datasetId: string) => `/api/experimental-data/${datasetId}/coverage`,
    ALL_COVERAGE: '/api/experimental-data/coverage/all',
  },
  
  // 覆盖率统计
  COVERAGE: {
    BATCH: (batchId: number) => `/api/coverage/batches/${batchId}`,
    ALL: '/api/coverage/all',
  }
} as const;

// ==================== 本地存储键 ====================

/**
 * LocalStorage 键名
 */
export const STORAGE_KEYS = {
  TOKEN: 'welding_token',
  USER: 'welding_user',
  CURRENT_DATASET: 'welding_current_dataset',
} as const;

// ==================== 分页配置 ====================

/**
 * 默认分页大小
 */
export const DEFAULT_PAGE_SIZE = 20;

/**
 * 分页大小选项
 */
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];

// ==================== 覆盖率配置 ====================

/**
 * 覆盖率阈值（百分比）
 */
export const COVERAGE_THRESHOLD = 90;

// ==================== 字段分类配置 ====================

/**
 * 字段分类显示名称
 */
export const CATEGORY_NAMES = {
  '物性': '物性参数',
  '工艺': '工艺参数',
  '状态': '状态参数',
  '性能': '性能指标',
  '其他': '其他参数',
} as const;

/**
 * 字段分类图标
 */
export const CATEGORY_ICONS = {
  '物性': '🧱',
  '工艺': '⚙️',
  '状态': '🌡️',
  '性能': '📈',
  '其他': '📁',
} as const;

/**
 * 字段分类颜色
 */
export const CATEGORY_COLORS = {
  '物性': '#1890ff',
  '工艺': '#52c41a',
  '状态': '#faad14',
  '性能': '#f5222d',
  '其他': '#8c8c8c',
} as const;

// ==================== UI 配置 ====================

/**
 * 侧边栏宽度
 */
export const SIDEBAR_WIDTH = 240;

/**
 * 头部高度
 */
export const HEADER_HEIGHT = 64;

/**
 * 消息提示持续时间（秒）
 */
export const MESSAGE_DURATION = 3;

/**
 * 文件上传限制
 */
export const UPLOAD_CONFIG = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ACCEPTED_TYPES: ['.csv', '.xlsx', '.xls'],
  ACCEPTED_MIME_TYPES: [
    'text/csv',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  ],
} as const;

// ==================== 角色权限 ====================

/**
 * 角色显示名称
 */
export const ROLE_NAMES = {
  root: '超级管理员',
  admin: '管理员',
  user: '普通用户',
} as const;
