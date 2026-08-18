# 启动 jwworkflow 后端（8081，使用 jwworkflow.db）
# 不使用 --reload（嵌套双 uvicorn 会导致 reload 失效）
cd D:\AI\opc\jwworkflow\backend
$env:DATABASE_URL = "sqlite+aiosqlite:///./jwworkflow.db"
# 用 python -m 启动：-m 会把当前目录加入 sys.path，避免 uvicorn.exe 找不到 app 模块
python -m uvicorn app.main:app --host 0.0.0.0 --port 8081
