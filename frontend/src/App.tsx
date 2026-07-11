import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ConfigProvider } from "antd"
import zhCN from "antd/locale/zh_CN"
import LoginPage from "./pages/LoginPage"
import WorkflowListPage from "./pages/WorkflowListPage"

const App = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/workflows" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/workflows" element={<WorkflowListPage />} />
          <Route path="/workflows/new" element={<div>新建工作流</div>} />
          <Route path="/workflows/:id" element={<div>工作流编辑器</div>} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
