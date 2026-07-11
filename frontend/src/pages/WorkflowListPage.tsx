import { Typography } from 'antd';

const { Title } = Typography;

const WorkflowListPage = () => {
  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>工作流列表</Title>
      <div style={{ marginTop: 16, color: '#999' }}>暂无工作流</div>
    </div>
  );
};

export default WorkflowListPage;
