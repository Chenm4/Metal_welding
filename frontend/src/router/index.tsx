/**
 * 路由配置
 * 定义应用的所有路由
 */
import { createBrowserRouter, Navigate } from 'react-router-dom';
import PrivateRoute from '@/components/PrivateRoute/PrivateRoute';
import Login from '@/pages/Login/Login';
import MainLayout from '@/layouts/MainLayout/MainLayout';
import DataManagement from '@/pages/DataManagement/DataManagement';
import CoverageOverview from '@/pages/CoverageOverview/CoverageOverview';
import UserManagement from '@/pages/UserManagement/UserManagement';
import WeldingVisualization from '@/pages/WeldingVisualization/WeldingVisualization';

/**
 * 路由配置
 */
export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/',
    element: (
      <PrivateRoute>
        <MainLayout />
      </PrivateRoute>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dataset" replace />,
      },
      {
        path: 'dataset/:datasetId',
        element: <DataManagement />,
      },
      {
        path: 'dataset',
        element: <Navigate to="/coverage" replace />,
      },
      {
        path: 'coverage',
        element: <CoverageOverview />,
      },
      {
        path: 'welding-visualization',
        element: <WeldingVisualization />,
      },
      {
        path: 'users',
        element: <UserManagement />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
