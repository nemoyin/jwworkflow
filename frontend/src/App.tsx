import React from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { ConfigProvider } from "antd"
import zhCN from "antd/locale/zh_CN"

const App: React.FC = () => {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<div>jwworkflow</div>} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  )
}

export default App
