# 后端镜像：FastAPI + 内置 SQLite 数据快照（模板、实例化工作流、对话记录等固化在镜像内）
# 构建上下文：./backend
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# 容器内实测：清华源 SSL 被阻断、官方源超时；阿里云镜像稳定可达
RUN pip install --no-cache-dir --default-timeout=120 \
    -i https://mirrors.aliyun.com/pypi/simple/ \
    -r requirements.txt

# 应用代码
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./
COPY pyproject.toml ./

# 持久化数据：上传/知识库目录 + SQLite 数据库快照
COPY data ./data
COPY data/jwworkflow.db ./jwworkflow.db

# 运行时环境（SQLite 绝对路径需 4 斜杠）
ENV DATABASE_URL=sqlite+aiosqlite:////app/jwworkflow.db
ENV JWT_SECRET=test-secret-for-development
ENV LLM_API_KEY=sk-dc42126e667a4e899fa68fc3f70b00b7
ENV LLM_BASE_URL=https://api.deepseek.com
ENV LLM_DEFAULT_MODEL=deepseek-v4-pro
ENV UPLOAD_DIR=./data/uploads
ENV KNOWLEDGE_DIR=./data/knowledge

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
