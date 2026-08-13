# 启动 jwworkflow 前端（5173，API 代理到 8081）
cd D:\AI\opc\jwworkflow\frontend
$env:VITE_API_PROXY = "http://localhost:8081"
npm run dev
