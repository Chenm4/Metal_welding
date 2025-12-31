/**
 * 认证相关 API 服务
 * 提供登录、获取用户信息等接口
 */

import { get, post, del, put } from '@/utils/request';
import { API_ENDPOINTS } from '@/config/constants';
import type { LoginRequest, LoginResponse, User } from '@/types';

/**
 * 用户登录
 */
export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  // 后端接受 JSON 格式
  return post<LoginResponse>(API_ENDPOINTS.AUTH.LOGIN, credentials);
};

/**
 * 获取当前登录用户信息
 */
export const getCurrentUser = async (): Promise<User> => {
  return get<User>(API_ENDPOINTS.AUTH.CURRENT_USER);
};

/**
 * 获取用户列表（管理员权限）
 */
export const getUserList = async (): Promise<any> => {
  return get<any>(API_ENDPOINTS.AUTH.USERS);
};

/**
 * 创建用户（管理员权限）
 */
export const createUser = async (userData: { username: string; password: string; role: string }): Promise<any> => {
  return post<any>(API_ENDPOINTS.AUTH.USERS, userData);
};

/**
 * 删除用户（管理员权限）
 */
export const deleteUser = async (userId: number): Promise<any> => {
  return del<any>(`/api/auth/users/${userId}`);
};

/**
 * 更新用户信息（管理员权限）
 */
export const updateUser = async (userId: number, userData: { 
  username?: string; 
  role?: string; 
  status?: string;
  password?: string;
}): Promise<any> => {
  return put<any>(`/api/auth/users/${userId}`, userData);
};

/**
 * 更新用户状态（管理员权限）
 */
export const updateUserStatus = async (userId: number, isActive: boolean): Promise<any> => {
  return post<any>(`/api/auth/users/${userId}/status`, { is_active: isActive });
};
