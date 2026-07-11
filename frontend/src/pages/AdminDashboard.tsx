import React, { useEffect, useState } from 'react';
import {
  Card, Table, Button, Modal, Form, Input, Select, Switch, Space, Tag,
  message, Popconfirm, Tabs, Typography, Descriptions,
} from 'antd';
import { UserOutlined, TeamOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons';
import { api } from '../services/api';

interface TenantInfo {
  id: string; name: string; slug: string; plan: string; created_at: string;
  users?: Array<{ id: string; email: string; display_name: string; role: string; is_active: boolean }>;
}

interface UserInfo {
  id: string; email: string; display_name: string; role: string; is_active: boolean; created_at: string;
}

const AdminDashboard: React.FC = () => {
  const [tenants, setTenants] = useState<TenantInfo[]>([]);
  const [users, setUsers] = useState<UserInfo[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedTenant, setSelectedTenant] = useState<TenantInfo | null>(null);
  const [tenantModal, setTenantModal] = useState(false);
  const [userModal, setUserModal] = useState(false);
  const [userForm] = Form.useForm();

  const loadData = async () => {
    setLoading(true);
    try {
      const [tData, uData] = await Promise.all([
        api.get<TenantInfo[]>('/admin/tenants').catch(() => [] as TenantInfo[]),
        api.get<UserInfo[]>('/admin/users'),
      ]);
      setTenants(tData);
      setUsers(uData);
    } catch { /* ignore */ }
    setLoading(false);
  };

  useEffect(() => { loadData(); }, []);

  const viewTenant = async (id: string) => {
    try {
      const data = await api.get<TenantInfo>(`/admin/tenants/${id}`);
      setSelectedTenant(data);
      setTenantModal(true);
    } catch { message.error('加载失败'); }
  };

  const handleAddUser = async () => {
    const values = await userForm.validateFields();
    try {
      await api.post('/admin/users', values);
      message.success('用户已添加');
      setUserModal(false);
      userForm.resetFields();
      loadData();
    } catch { message.error('添加失败'); }
  };

  const handleUpdateUser = async (id: string, body: any) => {
    try {
      await api.put(`/admin/users/${id}`, body);
      message.success('已更新');
      loadData();
    } catch { message.error('更新失败'); }
  };

  const handleDeleteUser = async (id: string) => {
    try {
      await api.delete(`/admin/users/${id}`);
      message.success('已删除');
      loadData();
    } catch { message.error('删除失败'); }
  };

  // --- Tenant columns (admin only) ---
  const tenantColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '标识', dataIndex: 'slug', key: 'slug' },
    { title: '套餐', dataIndex: 'plan', key: 'plan', render: (v: string) => <Tag>{v || 'free'}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (v: string) => v?.substring(0, 10) },
    {
      title: '操作', key: 'action',
      render: (_: any, r: TenantInfo) => (
        <Button size="small" onClick={() => viewTenant(r.id)}>查看详情</Button>
      ),
    },
  ];

  // --- User columns ---
  const userColumns = [
    { title: '邮箱', dataIndex: 'email', key: 'email' },
    { title: '显示名', dataIndex: 'display_name', key: 'display_name' },
    {
      title: '角色', dataIndex: 'role', key: 'role',
      render: (v: string) => <Tag color={v === 'admin' ? 'red' : 'blue'}>{v === 'admin' ? '管理员' : '成员'}</Tag>,
    },
    {
      title: '状态', dataIndex: 'is_active', key: 'is_active',
      render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '激活' : '禁用'}</Tag>,
    },
    {
      title: '操作', key: 'action', width: 200,
      render: (_: any, r: UserInfo) => (
        <Space>
          <Select
            size="small"
            value={r.role}
            style={{ width: 80 }}
            onChange={(v) => handleUpdateUser(r.id, { role: v })}
            options={[{ value: 'admin', label: 'Admin' }, { value: 'member', label: 'Member' }]}
          />
          <Switch
            size="small"
            checked={r.is_active}
            onChange={(v) => handleUpdateUser(r.id, { is_active: v })}
          />
          <Popconfirm title="确定删除？" onConfirm={() => handleDeleteUser(r.id)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={4}><TeamOutlined /> 管理后台</Typography.Title>
      <Tabs defaultActiveKey="users" items={[
        // Users tab (available to all tenants)
        {
          key: 'users',
          label: <span><UserOutlined /> 用户管理</span>,
          children: (
            <Card extra={
              <Button type="primary" icon={<PlusOutlined />} onClick={() => {
                userForm.resetFields(); setUserModal(true);
              }}>添加用户</Button>
            }>
              <Table dataSource={users} columns={userColumns} rowKey="id" loading={loading} pagination={false} />
            </Card>
          ),
        },
        // Tenants tab (super admin only, data may be empty for non-admin)
        {
          key: 'tenants',
          label: <span><TeamOutlined /> 租户管理</span>,
          children: (
            <Card>
              <Table dataSource={tenants} columns={tenantColumns} rowKey="id" loading={loading} pagination={false} />
            </Card>
          ),
        },
      ]} />

      {/* Tenant Detail Modal */}
      <Modal title="租户详情" open={tenantModal} footer={null}
        onCancel={() => setTenantModal(false)} width={600}>
        {selectedTenant && (
          <div>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="名称">{selectedTenant.name}</Descriptions.Item>
              <Descriptions.Item label="标识">{selectedTenant.slug}</Descriptions.Item>
              <Descriptions.Item label="套餐">{selectedTenant.plan}</Descriptions.Item>
              <Descriptions.Item label="创建时间">{selectedTenant.created_at}</Descriptions.Item>
            </Descriptions>
            <Typography.Title level={5} style={{ marginTop: 16, fontSize: 13 }}>用户列表</Typography.Title>
            <Table
              dataSource={selectedTenant.users || []}
              columns={[
                { title: '邮箱', dataIndex: 'email' },
                { title: '角色', dataIndex: 'role', render: (v: string) => <Tag>{v}</Tag> },
                { title: '状态', dataIndex: 'is_active', render: (v: boolean) => v ? '✅' : '❌' },
              ]}
              rowKey="id"
              pagination={false}
              size="small"
            />
          </div>
        )}
      </Modal>

      {/* Add User Modal */}
      <Modal title="添加用户" open={userModal}
        onOk={handleAddUser} onCancel={() => { setUserModal(false); userForm.resetFields(); }}>
        <Form form={userForm} layout="vertical">
          <Form.Item name="email" label="邮箱" rules={[{ required: true, type: 'email' }]}>
            <Input placeholder="user@example.com" />
          </Form.Item>
          <Form.Item name="password" label="初始密码">
            <Input.Password placeholder="Default123!@#" />
          </Form.Item>
          <Form.Item name="role" label="角色" initialValue="member">
            <Select options={[{ value: 'admin', label: '管理员' }, { value: 'member', label: '成员' }]} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AdminDashboard;
