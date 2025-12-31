/**
 * AuthContext - 认证状态管理
 * 提供全局的用户认证状态和相关操作
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';
import { getToken, getUser, clearAuth, saveUser as saveUserToStorage } from '@/utils/storage';
import { getCurrentUser } from '@/services/auth';
import type { User } from '@/types';

/**
 * 认证上下文值接口
 */
interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isRoot: boolean;
  login: (user: User) => void;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

/**
 * 创建认证上下文
 */
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

/**
 * 认证提供者组件 Props
 */
interface AuthProviderProps {
  children: ReactNode;
}

/**
 * 认证提供者组件
 * 管理全局认证状态，自动从 localStorage 恢复登录状态
 */
export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  /**
   * 初始化：从 localStorage 恢复用户状态
   */
  useEffect(() => {
    const initAuth = async () => {
      const token = getToken();
      const cachedUser = getUser();

      if (token && cachedUser) {
        // 有 Token 和缓存用户信息，尝试刷新用户信息
        try {
          const freshUser = await getCurrentUser();
          setUser(freshUser);
          saveUserToStorage(freshUser);
        } catch (error) {
          // Token 可能已过期，清除认证信息
          console.error('获取用户信息失败:', error);
          clearAuth();
          setUser(null);
        }
      }

      setLoading(false);
    };

    initAuth();
  }, []);

  /**
   * 登录：设置用户信息
   */
  const login = (newUser: User) => {
    setUser(newUser);
  };

  /**
   * 登出：清除所有认证信息
   */
  const logout = () => {
    clearAuth();
    setUser(null);
  };

  /**
   * 刷新用户信息
   */
  const refreshUser = async () => {
    try {
      const freshUser = await getCurrentUser();
      setUser(freshUser);
      saveUserToStorage(freshUser);
    } catch (error) {
      console.error('刷新用户信息失败:', error);
      throw error;
    }
  };

  /**
   * 计算认证状态
   */
  const isAuthenticated = !!user;
  const isAdmin = user?.role === 'admin' || user?.role === 'root';
  const isRoot = user?.role === 'root';

  const value: AuthContextValue = {
    user,
    loading,
    isAuthenticated,
    isAdmin,
    isRoot,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

/**
 * 使用认证上下文的 Hook
 * 必须在 AuthProvider 内部使用
 */
export const useAuth = (): AuthContextValue => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth 必须在 AuthProvider 内部使用');
  }
  return context;
};
