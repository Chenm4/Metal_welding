/**
 * App 根组件
 * 提供路由和全局状态管理
 */

import React from 'react';
import { RouterProvider } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import zhCN from 'antd/locale/zh_CN';
import { AuthProvider } from '@/contexts/AuthContext';
import { router } from '@/router';
import 'dayjs/locale/zh-cn';

/**
 * Ant Design 主题配置
 */
const theme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 8,
    fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  },
};

/**
 * App 根组件
 */
const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN} theme={theme}>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </ConfigProvider>
  );
};

export default App;
