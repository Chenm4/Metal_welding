/**
 * 用户管理页面
 * 仅管理员可见，展示系统用户列表
 */

import React, { useState, useEffect, useMemo } from 'react';
import { Card, Table, Tag, Typography, message, Space, Avatar, Button, Modal, Form, Input, Select, Popconfirm, Radio, Checkbox } from 'antd';
import { UserOutlined, SafetyCertificateOutlined, PlusOutlined, DeleteOutlined, CrownOutlined, SearchOutlined, EditOutlined } from '@ant-design/icons';
import { getUserList, createUser, deleteUser, updateUser } from '@/services/auth';
import { useAuth } from '@/contexts/AuthContext';
import { ROLE_NAMES } from '@/config/constants';
import type { User, UserRole } from '@/types';
import type { TablePaginationConfig } from 'antd';
import './UserManagement.css';

const { Title } = Typography;
const { Search } = Input;

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [searchKeyword, setSearchKeyword] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('all');
  const [pagination, setPagination] = useState<TablePaginationConfig>({
    current: 1,
    pageSize: 10,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total) => `共 ${total} 个用户`,
  });
  const { user: currentUser, isRoot } = useAuth();
  const [form] = Form.useForm();
  const [editForm] = Form.useForm();

  useEffect(() => {
    loadUsers();
  }, [isRoot]);

  const loadUsers = async () => {
    setLoading(true);
    try {
      const response = await getUserList();
      console.log('User list response:', response);
      
      let userList: User[] = [];
      if (Array.isArray(response)) {
        userList = response;
      } else if (response && (response as any).data) {
        userList = (response as any).data;
      } else if (response && (response as any).users) {
        userList = (response as any).users;
      } else {
        console.error('Unexpected response format:', response);
        message.error('用户数据格式异常');
        return;
      }
      
      console.log('Parsed user list:', userList);
      console.log('First user sample:', userList[0]);
      
      // root 可以看到所有用户，admin 只能看到 user
      const filteredUsers = isRoot 
        ? userList 
        : userList.filter(u => u.role === 'user');
      
      setUsers(filteredUsers);
      setPagination(prev => ({ ...prev, total: filteredUsers.length }));
    } catch (error: any) {
      console.error('加载用户列表失败:', error);
      message.error(error.response?.data?.detail || '加载用户列表失败');
    } finally {
      setLoading(false);
    }
  };

  /**
   * 过滤后的用户列表
   */
  const filteredUsers = useMemo(() => {
    let result = users;
    
    // 角色筛选
    if (roleFilter !== 'all') {
      result = result.filter(user => user.role === roleFilter);
    }
    
    // 搜索筛选
    if (searchKeyword) {
      result = result.filter(user => 
        user.username.toLowerCase().includes(searchKeyword.toLowerCase())
      );
    }
    
    return result;
  }, [users, roleFilter, searchKeyword]);

  /**
   * 处理搜索
   */
  const handleSearch = (value: string) => {
    setSearchKeyword(value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  /**
   * 处理角色筛选
   */
  const handleRoleFilterChange = (e: any) => {
    setRoleFilter(e.target.value);
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  /**
   * 处理分页变化
   */
  const handleTableChange = (newPagination: TablePaginationConfig) => {
    setPagination(newPagination);
  };

  const handleCreateUser = async () => {
    try {
      const values = await form.validateFields();
      await createUser(values);
      message.success('用户创建成功');
      setModalVisible(false);
      form.resetFields();
      loadUsers();
    } catch (error: any) {
      console.error('创建用户失败:', error);
      if (!error.errorFields) {
        message.error(error.response?.data?.detail || '创建用户失败');
      }
    }
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await deleteUser(userId);
      message.success('用户删除成功');
      loadUsers();
    } catch (error: any) {
      console.error('删除用户失败:', error);
      message.error(error.response?.data?.detail || '删除用户失败');
    }
  };

  /**
   * 打开编辑模态框
   */
  const handleEdit = (user: User) => {
    console.log('开始编辑用户:', user);
    setEditingUser(user);
    const status = (user as any).status || 'active';
    const formData = {
      username: user.username,
      role: user.role,
      is_active: status === 'active',
      password: undefined, // 清空密码字段
    };
    console.log('设置表单初始值:', formData);
    editForm.setFieldsValue(formData);
    setEditModalVisible(true);
  };

  /**
   * 处理编辑用户
   */
  const handleUpdateUser = async () => {
    if (!editingUser) {
      message.error('未选择要编辑的用户');
      return;
    }
    
    try {
      const values = await editForm.validateFields();
      console.log('表单验证通过，提交的值:', values);
      
      const updateData: any = {
        username: values.username,
        role: values.role,
        status: values.is_active ? 'active' : 'disabled',
      };
      
      // 如果输入了密码，则重置密码
      if (values.password && values.password.trim()) {
        updateData.password = values.password;
      }
      
      console.log('准备更新用户，用户ID:', editingUser.id, '更新数据:', updateData);
      
      await updateUser(editingUser.id, updateData);
      message.success('用户信息更新成功');
      setEditModalVisible(false);
      setEditingUser(null);
      editForm.resetFields();
      loadUsers();
    } catch (error: any) {
      console.error('更新用户失败，详细错误:', error);
      if (error.errorFields) {
        console.error('表单验证失败:', error.errorFields);
      } else if (error.response) {
        console.error('API 响应错误:', error.response);
        message.error(error.response?.data?.detail || error.response?.data?.message || '更新用户失败');
      } else {
        message.error('更新用户失败: ' + (error.message || '未知错误'));
      }
    }
  };

  const columns = [
    {
      title: '用户名',
      dataIndex: 'username',
      key: 'username',
      align: 'center' as const,
      render: (text: string, record: User) => {
        const avatarColor = 
          record.role === 'root' ? '#722ed1' : 
          record.role === 'admin' ? '#1890ff' : 
          '#87d068';
        return (
          <Space>
            <Avatar icon={<UserOutlined />} style={{ backgroundColor: avatarColor }} />
            <span style={{ fontWeight: 'bold' }}>{text}</span>
          </Space>
        );
      },
    },
    {
      title: '角色',
      dataIndex: 'role',
      key: 'role',
      align: 'center' as const,
      render: (role: string) => {
        const config = {
          root: { color: 'purple', icon: <CrownOutlined /> },
          admin: { color: 'blue', icon: <SafetyCertificateOutlined /> },
          user: { color: 'green', icon: null }
        };
        const { color, icon } = config[role as UserRole] || { color: 'default', icon: null };
        return (
          <Tag color={color} icon={icon}>
            {ROLE_NAMES[role as keyof typeof ROLE_NAMES] || role}
          </Tag>
        );
      },
    },
    {
      title: '状态',
      key: 'status',
      align: 'center' as const,
      render: (record: User) => {
        const status = (record as any).status || 'active';
        const isActive = status === 'active';
        return (
          <Tag color={isActive ? 'success' : 'error'}>
            {isActive ? '正常' : '已禁用'}
          </Tag>
        );
      },
    },
    {
      title: '操作',
      key: 'action',
      align: 'center' as const,
      render: (_: any, record: User) => {
        // 不能删除或编辑自己
        const isSelf = currentUser?.id === record.id;
        
        // 权限控制：root 可以编辑所有用户，admin 可以编辑 user
        const canEdit = !isSelf && (
          isRoot || 
          (currentUser?.role === 'admin' && record.role === 'user')
        );
        
        return (
          <Space size="small">
            {canEdit && (
              <Button 
                type="link" 
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              >
                编辑
              </Button>
            )}
            <Popconfirm
              title="确认删除该用户吗？"
              onConfirm={() => handleDeleteUser(record.id)}
              okText="确认"
              cancelText="取消"
              disabled={isSelf}
            >
              <Button 
                type="link" 
                danger 
                icon={<DeleteOutlined />}
                disabled={isSelf}
              >
                删除
              </Button>
            </Popconfirm>
          </Space>
        );
      },
    },
  ];

  return (
    <div className="user-management">
      <Card>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <Title level={3}>👥 用户管理</Title>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setModalVisible(true)}>
            新增用户
          </Button>
        </div>

        {/* 筛选和搜索栏 */}
        <div style={{ marginBottom: 16, display: 'flex', gap: 16, alignItems: 'center' }}>
          <Space>
            <span>角色筛选:</span>
            <Radio.Group value={roleFilter} onChange={handleRoleFilterChange}>
              <Radio.Button value="all">全部</Radio.Button>
              {isRoot && <Radio.Button value="root">超级管理员</Radio.Button>}
              <Radio.Button value="admin">管理员</Radio.Button>
              <Radio.Button value="user">普通用户</Radio.Button>
            </Radio.Group>
          </Space>
          <Search
            placeholder="搜索用户名"
            allowClear
            onSearch={handleSearch}
            onChange={(e) => handleSearch(e.target.value)}
            style={{ width: 250 }}
            enterButton={<SearchOutlined />}
          />
        </div>

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={pagination}
          onChange={handleTableChange}
        />
      </Card>

      <Modal
        title="新增用户"
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
        }}
        onOk={handleCreateUser}
        okText="创建"
        cancelText="取消"
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名最多50个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="password"
            label="密码"
            rules={[
              { required: true, message: '请输入密码' },
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="请输入密码" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
            initialValue="user"
          >
            <Select>
              {/* root 可以创建所有角色 */}
              {isRoot && (
                <>
                  <Select.Option value="root">超级管理员</Select.Option>
                  <Select.Option value="admin">管理员</Select.Option>
                </>
              )}
              {/* admin 和 root 都可以创建普通用户 */}
              <Select.Option value="user">普通用户</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑用户模态框 */}
      <Modal
        title="编辑用户"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingUser(null);
          editForm.resetFields();
        }}
        onOk={handleUpdateUser}
        okText="保存"
        cancelText="取消"
      >
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="username"
            label="用户名"
            rules={[
              { required: true, message: '请输入用户名' },
              { min: 3, message: '用户名至少3个字符' },
              { max: 50, message: '用户名最多50个字符' },
            ]}
          >
            <Input placeholder="请输入用户名" />
          </Form.Item>
          <Form.Item
            name="role"
            label="角色"
            rules={[{ required: true, message: '请选择角色' }]}
          >
            <Select>
              {/* root 可以修改所有角色 */}
              {isRoot && (
                <>
                  <Select.Option value="root">超级管理员</Select.Option>
                  <Select.Option value="admin">管理员</Select.Option>
                </>
              )}
              <Select.Option value="user">普通用户</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item
            name="is_active"
            label="状态"
            valuePropName="checked"
          >
            <Checkbox>启用该用户</Checkbox>
          </Form.Item>
          <Form.Item
            name="password"
            label="重置密码（选填）"
            rules={[
              { min: 6, message: '密码至少6个字符' },
            ]}
          >
            <Input.Password placeholder="不修改密码请留空" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;
