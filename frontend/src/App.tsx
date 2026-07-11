import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ConfigProvider } from "antd"
import zhCN from "antd/locale/zh_CN"
import LoginPage from "./pages/LoginPage"
import WorkflowListPage from "./pages/WorkflowListPage"
import WorkflowEditorPage from "./pages/WorkflowEditorPage"
import RunHistoryPage from "./pages/RunHistoryPage"
import AuthGuard from "./components/layout/AuthGuard"
import AppLayout from "./components/layout/AppLayout"

const App = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route element={<AuthGuard />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<Navigate to="/workflows" replace />} />
              <Route path="/workflows" element={<WorkflowListPage />} />
              <Route path="/workflows/new" element={<WorkflowEditorPage />} />
              <Route path="/workflows/:id" element={<WorkflowEditorPage />} />
              <Route path="/history" element={<RunHistoryPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
