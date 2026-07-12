import { useState } from 'react';
import { Layout, Menu, Button, Typography, theme } from 'antd';
import {
  PartitionOutlined, BookOutlined, HistoryOutlined, AppstoreOutlined,
  ApiOutlined, SettingOutlined, ThunderboltOutlined,
  MenuFoldOutlined, MenuUnfoldOutlined, LogoutOutlined,
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuthStore } from '../../stores/authStore';

const { Header, Sider, Content } = Layout;
const { Text } = Typography;

const AppLayout = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const userEmail = useAuthStore((state) => state.userEmail);
  const logout = useAuthStore((state) => state.logout);
  const { token: { colorBgContainer } } = theme.useToken();

  const menuItems = [
    {
      key: '/workflows',
      icon: <PartitionOutlined />,
      label: '工作流列表',
    },
    {
      key: '/knowledge',
      icon: <BookOutlined />,
      label: '知识库',
    },
    {
      key: '/history',
      icon: <HistoryOutlined />,
      label: '运行历史',
    },
    {
      key: '/templates',
      icon: <AppstoreOutlined />,
      label: '模板市场',
    },
    {
      key: '/admin/models',
      icon: <ApiOutlined />,
      label: '模型管理',
    },
    {
      key: '/tools',
      icon: <ApiOutlined />,
      label: '工具市场',
    },
    {
      key: '/analytics',
      icon: <ThunderboltOutlined />,
      label: '分析',
    },
    {
      key: '/admin',
      icon: <SettingOutlined />,
      label: '管理后台',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
        <div
          style={{
            height: 32,
            margin: 16,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          <Text
            strong
            style={{
              color: '#fff',
              fontSize: collapsed ? 14 : 18,
              whiteSpace: 'nowrap',
            }}
          >
            {collapsed ? 'JW' : 'jwworkflow'}
          </Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
        />
      </Sider>
      <Layout>
        <Header
          style={{
            padding: '0 24px',
            background: colorBgContainer,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
            <Text>{userEmail || '用户'}</Text>
            <Button type="text" icon={<LogoutOutlined />} onClick={handleLogout}>
              退出
            </Button>
          </div>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
};

export default AppLayout;
