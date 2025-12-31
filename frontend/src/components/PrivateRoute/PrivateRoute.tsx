/**
 * PrivateRoute - 私有路由组件
 * 保护需要登录才能访问的页面
 */

import React from 'react';
import { Navigate } from 'react-router-dom';
import { Spin } from 'antd';
import { useAuth } from '@/contexts/AuthContext';

/**
 * 私有路由组件 Props
 */
interface PrivateRouteProps {
  children: React.ReactElement;
  requireAdmin?: boolean; // 是否需要管理员权限
}

/**
 * 私有路由组件
 * 未登录用户重定向到登录页
 * 非管理员用户访问管理员页面时显示提示
 */
const PrivateRoute: React.FC<PrivateRouteProps> = ({ 
  children, 
  requireAdmin = false 
}) => {
  const { isAuthenticated, isAdmin, loading } = useAuth();

  // 加载中显示 Spin
  if (loading) {
    return (
      <div style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center', 
        height: '100vh' 
      }}>
        <Spin size="large" tip="正在加载..." />
      </div>
    );
  }

  // 未登录，重定向到登录页
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // 需要管理员权限但用户不是管理员
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/" replace />;
  }

  return children;
};

export default PrivateRoute;
