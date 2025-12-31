/**
 * 登录页面组件
 * 提供用户登录功能
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Form, Input, Button, Card, message, Typography } from 'antd';
import { UserOutlined, LockOutlined, DatabaseOutlined } from '@ant-design/icons';
import { login } from '@/services/auth';
import { saveToken, saveUser } from '@/utils/storage';
import { useAuth } from '@/contexts/AuthContext';
import type { LoginRequest } from '@/types';
import './Login.css';

const { Title, Text } = Typography;

/**
 * 登录页面组件
 */
const Login: React.FC = () => {
  const navigate = useNavigate();
  const { login: setAuthUser } = useAuth();
  const [loading, setLoading] = useState(false);

  /**
   * 处理登录表单提交
   */
  const handleLogin = async (values: LoginRequest) => {
    setLoading(true);
    try {
      const response = await login(values);
      
      // 保存 Token 和用户信息到 localStorage
      saveToken(response.access_token);
      saveUser(response.user);
      
      // 更新 AuthContext 状态
      setAuthUser(response.user);

      message.success('登录成功！');
      
      // 跳转到主页
      navigate('/', { replace: true });
    } catch (error) {
      // 错误已在 request.ts 中统一处理
      console.error('登录失败:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-background" />
      <Card className="login-card" bordered={false}>
        <div className="login-header">
          <DatabaseOutlined className="login-icon" />
          <Title level={2} className="login-title">
            焊接数据库系统
          </Title>
          <Text type="secondary">Metal Welding Database System</Text>
        </div>

        <Form
          name="login"
          initialValues={{ username: '', password: '' }}
          onFinish={handleLogin}
          size="large"
          className="login-form"
        >
          <Form.Item
            name="username"
            rules={[{ required: true, message: '请输入用户名！' }]}
          >
            <Input
              prefix={<UserOutlined />}
              placeholder="用户名"
              autoComplete="username"
            />
          </Form.Item>

          <Form.Item
            name="password"
            rules={[{ required: true, message: '请输入密码！' }]}
          >
            <Input.Password
              prefix={<LockOutlined />}
              placeholder="密码"
              autoComplete="current-password"
            />
          </Form.Item>

          <Form.Item>
            <Button
              type="primary"
              htmlType="submit"
              className="login-button"
              loading={loading}
              block
            >
              登录
            </Button>
          </Form.Item>
        </Form>

        <div className="login-tips">
          <Text type="secondary" style={{ fontSize: 12 }}>
            💡 提示：管理员账号可以进行数据管理，普通用户只能查看数据
          </Text>
        </div>
      </Card>
    </div>
  );
};

export default Login;
