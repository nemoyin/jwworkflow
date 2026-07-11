import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ConfigProvider } from "antd"
import zhCN from "antd/locale/zh_CN"
import LoginPage from "./pages/LoginPage"
import WorkflowListPage from "./pages/WorkflowListPage"
import WorkflowEditorPage from "./pages/WorkflowEditorPage"

const App = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/workflows" replace />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/workflows" element={<WorkflowListPage />} />
          <Route path="/workflows/new" element={<WorkflowEditorPage />} />
          <Route path="/workflows/:id" element={<WorkflowEditorPage />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
