/**
 * 主布局组件
 * 包含侧边栏、头部、内容区域
 */

import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, Avatar, Dropdown, Typography, message } from 'antd';
import {
  DatabaseOutlined,
  UploadOutlined,
  LogoutOutlined,
  UserOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { getDatasetList } from '@/services/dataset';
import { saveCurrentDataset, getCurrentDataset } from '@/utils/storage';
import { ROLE_NAMES } from '@/config/constants';
import ImportModal from '@/components/ImportModal/ImportModal';
import type { Dataset } from '@/types';
import type { MenuProps } from 'antd';
import './MainLayout.css';

const { Sider, Header, Content } = Layout;
const { Text } = Typography;

/**
 * 主布局组件
 */
const MainLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAdmin, logout } = useAuth();

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [currentDatasetId, setCurrentDatasetId] = useState<string | null>(null);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [collapsed, setCollapsed] = useState(false);

  /**
   * 加载数据集列表
   */
  useEffect(() => {
    loadDatasets();
  }, []);

  /**
   * 从 URL 或 localStorage 恢复当前数据集
   */
  useEffect(() => {
    const pathParts = location.pathname.split('/');
    const isDatasetPath = pathParts[1] === 'dataset';
    const isRootPath = location.pathname === '/' || location.pathname === '/dataset';
    
    const pathDatasetId = isDatasetPath ? pathParts[2] : null;
    const cachedDatasetId = getCurrentDataset();

    if (pathDatasetId && datasets.some(d => d.id === pathDatasetId)) {
      setCurrentDatasetId(pathDatasetId);
      saveCurrentDataset(pathDatasetId);
    } else if (isRootPath) {
      if (cachedDatasetId && datasets.some(d => d.id === cachedDatasetId)) {
        setCurrentDatasetId(cachedDatasetId);
        navigate(`/dataset/${cachedDatasetId}`, { replace: true });
      } else if (datasets.length > 0) {
        // 默认选择第一个数据集
        const firstDataset = datasets[0];
        setCurrentDatasetId(firstDataset.id);
        saveCurrentDataset(firstDataset.id);
        navigate(`/dataset/${firstDataset.id}`, { replace: true });
      }
    } else if (!isDatasetPath) {
      // 如果不在数据集路径下，清除当前选中的数据集高亮
      setCurrentDatasetId(null);
    }
  }, [datasets, location.pathname, navigate]);

  /**
   * 加载数据集列表
   */
  const loadDatasets = async () => {
    try {
      const response = await getDatasetList();
      setDatasets(response.datasets);
    } catch (error) {
      console.error('加载数据集失败:', error);
      message.error('加载数据集列表失败');
    }
  };

  /**
   * 切换数据集
   */
  const handleDatasetChange = (datasetId: string) => {
    setCurrentDatasetId(datasetId);
    saveCurrentDataset(datasetId);
    navigate(`/dataset/${datasetId}`);
  };

  /**
   * 处理登出
   */
  const handleLogout = () => {
    logout();
    navigate('/login');
    message.success('已退出登录');
  };

  /**
   * 用户下拉菜单
   */
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'username',
      label: (
        <div style={{ padding: '8px 0' }}>
          <Text strong>{user?.username}</Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {user?.role ? ROLE_NAMES[user.role as keyof typeof ROLE_NAMES] : '普通用户'}
          </Text>
        </div>
      ),
      disabled: true,
    },
    { type: 'divider' },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: handleLogout,
    },
  ];

  /**
   * 侧边栏菜单项
   */
  const menuItems: MenuProps['items'] = [
    {
      key: 'coverage',
      icon: <BarChartOutlined />,
      label: '质量概览',
      onClick: () => {
        setCurrentDatasetId(null);
        navigate('/coverage');
      },
    },
    isAdmin && {
      key: 'users',
      icon: <UserOutlined />,
      label: '用户管理',
      onClick: () => {
        setCurrentDatasetId(null);
        navigate('/users');
      },
    },
    {
      key: 'datasets-group',
      label: '数据集列表',
      type: 'group',
      children: datasets.map(dataset => ({
        key: dataset.id,
        icon: <DatabaseOutlined />,
        label: dataset.display_name,
        onClick: () => handleDatasetChange(dataset.id),
      })),
    },
  ].filter(Boolean) as MenuProps['items'];

  return (
    <Layout className="main-layout">
      {/* 侧边栏 */}
      <Sider
        className="sidebar"
        width={240}
        theme="dark"
        collapsible
        collapsed={collapsed}
        onCollapse={value => setCollapsed(value)}
      >
        <div className="logo-area">
          <DatabaseOutlined className="logo-icon" />
          {!collapsed && <span className="logo-text">焊接数据库系统</span>}
        </div>

        <Menu
          mode="inline"
          theme="dark"
          selectedKeys={currentDatasetId ? [currentDatasetId] : [location.pathname.split('/')[1] || 'coverage']}
          items={menuItems}
          className="nav-menu"
        />

        {/* 管理员专属：导入按钮 */}
        {isAdmin && (
          <div className="import-btn-area">
            <Button
              icon={<UploadOutlined />}
              block
              className="btn-import-csv"
              onClick={() => setImportModalVisible(true)}
            >
              {!collapsed && '导入 CSV 文件'}
            </Button>
          </div>
        )}
      </Sider>

      {/* 主内容区 */}
      <Layout className="main-content-wrapper">
        {/* 头部 */}
        <Header className="header">
          <div className="breadcrumb">
            <Text type="secondary">
              首页 / 数据管理 / {datasets.find(d => d.id === currentDatasetId)?.display_name || ''}
            </Text>
          </div>

          <div className="user-info">
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <div style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8 }}>
                <Text>{user?.username}</Text>
                <Avatar icon={<UserOutlined />} style={{ backgroundColor: isAdmin ? '#1890ff' : '#87d068' }} />
              </div>
            </Dropdown>
          </div>
        </Header>

        {/* 内容区域 */}
        <Content className="content-body">
          <Outlet context={{ currentDatasetId, refreshDatasets: loadDatasets }} />
        </Content>
      </Layout>

      {/* 导入弹窗 */}
      {isAdmin && (
        <ImportModal
          visible={importModalVisible}
          currentDatasetId={currentDatasetId}
          datasets={datasets}
          onClose={() => setImportModalVisible(false)}
          onSuccess={() => {
            setImportModalVisible(false);
            loadDatasets();
          }}
        />
      )}
    </Layout>
  );
};

export default MainLayout;
