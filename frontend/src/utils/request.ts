/**
 * HTTP 请求工具
 * 基于 axios 封装，提供统一的请求/响应处理
 */

import axios, { AxiosError } from 'axios';
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { message } from 'antd';
import { API_BASE_URL, MESSAGE_DURATION } from '@/config/constants';
import { getToken, clearAuth } from '@/utils/storage';
import type { ApiError } from '@/types';
// import logger from '@/utils/logger';

/**
 * 创建 axios 实例
 */
const request: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * 请求拦截器
 * 自动添加 Authorization header
 */
request.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    console.error('请求拦截器错误:', error);
    return Promise.reject(error);
  }
);

/**
 * 响应拦截器
 * 统一处理错误响应
 */
request.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError<ApiError>) => {
    // 处理网络错误
    if (!error.response) {
      // logger.error('网络连接失败:', error);
      message.error('网络连接失败，请检查您的网络', MESSAGE_DURATION);
      return Promise.reject(error);
    }

    const { status, data } = error.response;
    const errorMessage = data?.detail || '请求失败';

    switch (status) {
      case 401:
        // Token 无效或过期
        message.error('登录已过期，请重新登录', MESSAGE_DURATION);
        clearAuth();
        // 跳转到登录页
        window.location.href = '/login';
        break;

      case 403:
        // 权限不足
        message.error('权限不足：' + errorMessage, MESSAGE_DURATION);
        break;

      case 404:
        // 资源不存在
        message.error('资源不存在：' + errorMessage, MESSAGE_DURATION);
        break;

      case 400:
        // 请求参数错误
        message.error('请求错误：' + errorMessage, MESSAGE_DURATION);
        break;

      case 500:
        // 服务器错误
        message.error('服务器错误：' + errorMessage, MESSAGE_DURATION);
        break;

      default:
        message.error(errorMessage, MESSAGE_DURATION);
    }

    return Promise.reject(error);
  }
);

/**
 * 导出请求方法
 */
export default request;

/**
 * GET 请求
 */
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get<T>(url, config).then((res) => res.data);
};

/**
 * POST 请求
 */
export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post<T>(url, data, config).then((res) => res.data);
};

/**
 * PUT 请求
 */
export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.put<T>(url, data, config).then((res) => res.data);
};

/**
 * DELETE 请求
 */
export const del = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.delete<T>(url, config).then((res) => res.data);
};

/**
 * 文件上传请求
 */
export const upload = <T = any>(url: string, formData: FormData): Promise<T> => {
  return request.post<T>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  }).then((res) => res.data);
};
