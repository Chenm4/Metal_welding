/**
 * 本地存储工具函数
 * 提供类型安全的 localStorage 操作
 */

import { STORAGE_KEYS } from '@/config/constants';
import type { User } from '@/types';

/**
 * 保存 Token 到本地存储
 */
export const saveToken = (token: string): void => {
  localStorage.setItem(STORAGE_KEYS.TOKEN, token);
};

/**
 * 获取本地存储的 Token
 */
export const getToken = (): string | null => {
  return localStorage.getItem(STORAGE_KEYS.TOKEN);
};

/**
 * 移除本地存储的 Token
 */
export const removeToken = (): void => {
  localStorage.removeItem(STORAGE_KEYS.TOKEN);
};

/**
 * 保存用户信息到本地存储
 */
export const saveUser = (user: User): void => {
  localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(user));
};

/**
 * 获取本地存储的用户信息
 */
export const getUser = (): User | null => {
  const userStr = localStorage.getItem(STORAGE_KEYS.USER);
  if (!userStr) return null;
  
  try {
    return JSON.parse(userStr) as User;
  } catch {
    return null;
  }
};

/**
 * 移除本地存储的用户信息
 */
export const removeUser = (): void => {
  localStorage.removeItem(STORAGE_KEYS.USER);
};

/**
 * 清除所有认证信息
 */
export const clearAuth = (): void => {
  removeToken();
  removeUser();
};

/**
 * 保存当前选中的数据集 ID
 */
export const saveCurrentDataset = (datasetId: string): void => {
  localStorage.setItem(STORAGE_KEYS.CURRENT_DATASET, datasetId);
};

/**
 * 获取当前选中的数据集 ID
 */
export const getCurrentDataset = (): string | null => {
  return localStorage.getItem(STORAGE_KEYS.CURRENT_DATASET);
};

/**
 * 移除当前数据集
 */
export const removeCurrentDataset = (): void => {
  localStorage.removeItem(STORAGE_KEYS.CURRENT_DATASET);
};
