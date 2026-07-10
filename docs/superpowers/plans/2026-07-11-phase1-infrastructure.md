# Phase 1: 基础设施 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建 jwworkflow 平台后端基础设施，包含 FastAPI 项目脚手架、数据库模型、JWT 认证、多租户中间件、Docker Compose 一键启动。

**Architecture:** 后端采用 FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL，前端使用 React 脚手架。项目根目录 `jwworkflow/` 下分 `backend/` 和 `frontend/` 两个子目录，通过 `docker-compose.yml` 统一编排。

**Tech Stack:** Python 3.11+, FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL 16, pgvector, PyJWT, bcrypt, pytest, Docker Compose

## Global Constraints

- 严格 TDD：先写测试 → 失败 → 实现 → 通过 → 重构
- 每个任务 ≤ 30 分钟
- 单元测试覆盖率 ≥ 80%
- 必须执行：lint → unit test → integration test → build
- 所有 commit 遵循 Conventional Commits：feat/fix/refactor/test/docs/chore
- 项目根目录：`D:\AI\opc\jwworkflow`
- 默认 shell 为 Git Bash，路径用 POSIX 风格（/d/AI/opc/jwworkflow）

---

### Task 1: 后端项目脚手架与配置

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/pyproject.toml`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_health.py`

**Interfaces:**
- Consumes: 无（第一个任务）
- Produces: `app/main.py` — FastAPI 实例，含 `/health` 端点；`app/config.py` — Settings 类加载环境变量

- [ ] **Step 1: 创建目录结构**

```bash
cd /d/AI/opc/jwworkflow
mkdir -p backend/app/api backend/app/engine backend/app/nodes backend/app/models backend/app/schemas backend/app/services backend/app/middleware backend/tests
touch backend/app/__init__.py
touch backend/app/api/__init__.py
touch backend/app/engine/__init__.py
touch backend/app/nodes/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/services/__init__.py
touch backend/app/middleware/__init__.py
touch backend/tests/__init__.py
```

- [ ] **Step 2: 写配置模块测试**

```python
# backend/tests/test_config.py
import pytest
from app.config import Settings

class TestSettings:
    def test_default_database_url(self):
        """验证默认 DATABASE_URL 存在"""
        settings = Settings(DATABASE_URL="postgresql://postgres:postgres@localhost:5432/jwworkflow")
        assert settings.DATABASE_URL is not None
        assert "postgresql" in settings.DATABASE_URL

    def test_jwt_secret_required(self):
        """验证 JWT_SECRET 必须设置"""
        with pytest.raises(Exception):
            Settings()  # 缺 JWT_SECRET 应该报错
```

- [ ] **Step 3: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
pip install pytest python-decouple pydantic-settings
pytest tests/test_config.py -v
```
Expected: ModuleNotFoundError / ImportError — `app.config` 还不存在

- [ ] **Step 4: 实现配置模块**

```python
# backend/app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "jwworkflow"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/jwworkflow"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 1440  # 24 hours
    MAX_FILE_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./data/uploads"
    KNOWLEDGE_DIR: str = "./data/knowledge"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

```python
# backend/app/main.py
from fastapi import FastAPI
from app.config import Settings

settings = Settings()
app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

```python
# backend/requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
psycopg2-binary==2.9.9
alembic==1.13.0
pydantic==2.9.0
pydantic-settings==2.5.0
python-jose[cryptography]==3.3.0
bcrypt==4.2.0
python-multipart==0.0.12
python-docx==1.1.2
PyPDF2==0.4.0
httpx==0.27.0
pytest==8.3.0
pytest-asyncio==0.24.0
```

- [ ] **Step 5: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_config.py -v
```
Expected: PASS

- [ ] **Step 6: 写健康检查测试**

```python
# backend/tests/test_health.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestHealth:
    def test_health_returns_ok(self):
        """验证 /health 返回 ok"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
```

- [ ] **Step 7: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/ -v
```
Expected: PASS (test_config + test_health)

- [ ] **Step 8: 创建 .env 示例文件**

```bash
cd /d/AI/opc/jwworkflow
cat > backend/.env.example << 'EOF'
JWT_SECRET=change-this-to-a-random-secret
DEBUG=true
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/jwworkflow
EOF
```

- [ ] **Step 9: 创建 .gitignore**

```bash
cd /d/AI/opc/jwworkflow
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*.egg-info/
.env
.venv/
venv/
node_modules/
dist/
build/
data/
.superpowers/
EOF
```

- [ ] **Step 10: Commit**

```bash
cd /d/AI/opc/jwworkflow
git init
git add -A
git commit -m "chore: initialize FastAPI project structure"
```

---

### Task 2: 数据库连接与会话管理

**Files:**
- Create: `backend/app/database.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_database.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/script.py.mako`

**Interfaces:**
- Consumes: `app.config.Settings.DATABASE_URL`
- Produces: `app.database.get_db()` — 异步数据库会话依赖

- [ ] **Step 1: 写数据库连接测试**

```python
# backend/tests/test_database.py
import pytest
from sqlalchemy import text
from app.database import engine, get_db

class TestDatabase:
    def test_engine_creation(self):
        """验证数据库引擎可以创建"""
        assert engine is not None

    @pytest.mark.asyncio
    async def test_db_session(self):
        """验证数据库会话可以建立连接"""
        async for session in get_db():
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1
            break  # 只测试一次连接
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_database.py -v
```
Expected: ImportError — `app.database` 还不存在

- [ ] **Step 3: 实现数据库模块**

```python
# backend/app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

# 将同步 URL 转换为异步 URL
async_db_url = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgresql+asyncpg://")

engine = create_async_engine(async_db_url, echo=settings.DEBUG)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **Step 4: 更新 main.py 注册启动关闭事件**

```python
# backend/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config import Settings
from app.database import engine, Base

settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建所有表（开发环境使用）
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时释放引擎
    await engine.dispose()

app = FastAPI(title=settings.APP_NAME, debug=settings.DEBUG, lifespan=lifespan)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 5: 初始化 Alembic**

```bash
cd /d/AI/opc/jwworkflow/backend
pip install alembic asyncpg
alembic init alembic
```

修改 `alembic/env.py` 中的数据库 URL：

```python
# backend/alembic/env.py
from app.config import settings
from app.database import Base

# 修改这行
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 添加这行
target_metadata = Base.metadata
```

- [ ] **Step 6: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_database.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/database.py backend/app/main.py backend/alembic/ backend/tests/test_database.py
git commit -m "feat: add database connection and session management"
```

---

### Task 3: Tenant 和 User 模型

**Files:**
- Create: `backend/app/models/tenant.py`
- Create: `backend/app/models/user.py`
- Update: `backend/app/models/__init__.py`
- Create: `backend/app/schemas/tenant.py`
- Create: `backend/app/schemas/user.py`
- Update: `backend/app/schemas/__init__.py`
- Modify: `backend/app/database.py` (Base 导入所有模型)
- Create: `backend/tests/test_models.py`

**Interfaces:**
- Consumes: `app.database.Base`, `app.database.get_db`
- Produces: `models.Tenant`, `models.User` — SQLAlchemy ORM 类；`schemas.TenantCreate`, `schemas.UserCreate`, `schemas.TokenResponse` — Pydantic 模型

- [ ] **Step 1: 写模型测试**

```python
# backend/tests/test_models.py
import pytest
from app.models.tenant import Tenant
from app.models.user import User

class TestTenantModel:
    def test_tenant_creation(self):
        """验证 Tenant 模型可以实例化"""
        tenant = Tenant(name="测试租户", slug="test-tenant")
        assert tenant.name == "测试租户"
        assert tenant.slug == "test-tenant"
        assert tenant.plan == "free"  # 默认值

class TestUserModel:
    def test_user_creation(self):
        """验证 User 模型可以实例化"""
        user = User(
            email="test@example.com",
            password_hash="hashed_pwd",
            role="member"
        )
        assert user.email == "test@example.com"
        assert user.role == "member"
        assert user.is_active is True  # 默认值
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_models.py -v
```
Expected: ImportError — 模型文件还不存在

- [ ] **Step 3: 实现 Tenant 模型**

```python
# backend/app/models/tenant.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from app.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = Column(String(255), nullable=False)
    slug: Mapped[str] = Column(String(64), unique=True, nullable=False, index=True)
    plan: Mapped[str] = Column(String(32), default="free")
    config: Mapped[dict] = Column(JSON, default=dict)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Tenant {self.slug}>"
```

```python
# backend/app/models/user.py
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = Column(UUID(as_uuid=True), ForeignKey("tenants.id"), nullable=False)
    email: Mapped[str] = Column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = Column(String(255), nullable=False)
    display_name: Mapped[str] = Column(String(128), default="")
    role: Mapped[str] = Column(String(32), default="member")  # admin | member
    is_active: Mapped[bool] = Column(Boolean, default=True)
    created_at: Mapped[datetime] = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    tenant = relationship("Tenant", backref="users")

    def __repr__(self):
        return f"<User {self.email}>"
```

- [ ] **Step 4: 更新 models/__init__.py**

```python
# backend/app/models/__init__.py
from app.models.tenant import Tenant
from app.models.user import User

__all__ = ["Tenant", "User"]
```

- [ ] **Step 5: 迁移数据库**

```bash
cd /d/AI/opc/jwworkflow/backend
alembic revision --autogenerate -m "add tenant and user models"
alembic upgrade head
```

- [ ] **Step 6: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_models.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/models/ backend/tests/test_models.py
git commit -m "feat: add Tenant and User database models"
```

---

### Task 4: JWT 认证 (注册/登录)

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/api/auth.py`
- Modify: `backend/app/main.py` (注册 auth 路由)
- Create: `backend/tests/test_auth.py`

**Interfaces:**
- Consumes: `app.models.User`, `app.models.Tenant`
- Produces: `POST /api/auth/register` → 创建租户+用户；`POST /api/auth/login` → JWT token；`get_current_user` 依赖

- [ ] **Step 1: 写认证测试**

```python
# backend/tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuth:
    REGISTER_DATA = {
        "tenant_name": "测试公司",
        "email": "admin@test.com",
        "password": "Test123!@#"
    }

    def test_register_success(self):
        """验证注册成功返回 token"""
        response = client.post("/api/auth/register", json=self.REGISTER_DATA)
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_success(self):
        """验证登录成功返回 token"""
        # 先注册
        client.post("/api/auth/register", json=self.REGISTER_DATA)
        # 再登录
        response = client.post("/api/auth/login", json={
            "email": self.REGISTER_DATA["email"],
            "password": self.REGISTER_DATA["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_login_wrong_password(self):
        """验证错误密码返回 401"""
        client.post("/api/auth/register", json=self.REGISTER_DATA)
        response = client.post("/api/auth/login", json={
            "email": self.REGISTER_DATA["email"],
            "password": "wrong_password"
        })
        assert response.status_code == 401
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_auth.py -v
```
Expected: 404 — API 路由不存在

- [ ] **Step 3: 实现 JWT 工具函数**

```python
# backend/app/services/auth_service.py
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError
from app.config import Settings

settings = Settings()

def hash_password(password: str) -> str:
    """使用 bcrypt 哈希密码"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

def create_access_token(data: dict) -> str:
    """创建 JWT token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    """解码 JWT token"""
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
```

```python
# backend/app/schemas/auth.py
from pydantic import BaseModel, EmailStr

class RegisterRequest(BaseModel):
    tenant_name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserInfo(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    tenant_id: str
```

- [ ] **Step 4: 实现认证 API**

```python
# backend/app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.tenant import Tenant
from app.models.user import User
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from app.services.auth_service import hash_password, verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=TokenResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """注册新租户和管理员用户"""
    # 检查邮箱是否已存在
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="邮箱已注册")

    # 创建租户
    tenant = Tenant(name=req.tenant_name, slug=req.tenant_name[:64])
    db.add(tenant)
    await db.flush()

    # 创建管理员用户
    user = User(
        tenant_id=tenant.id,
        email=req.email,
        password_hash=hash_password(req.password),
        display_name=req.email.split("@")[0],
        role="admin"
    )
    db.add(user)
    await db.flush()

    # 生成 token
    token = create_access_token({"sub": str(user.id), "tenant_id": str(tenant.id)})
    return TokenResponse(access_token=token)

@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="邮箱或密码错误")

    token = create_access_token({"sub": str(user.id), "tenant_id": str(user.tenant_id)})
    return TokenResponse(access_token=token)
```

- [ ] **Step 5: 注册路由到 main.py**

```python
# 在 backend/app/main.py 中添加
from app.api import auth as auth_router
app.include_router(auth_router.router)
```

- [ ] **Step 6: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_auth.py -v
```
Expected: PASS

- [ ] **Step 7: Commit**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/services/ backend/app/schemas/auth.py backend/app/api/auth.py backend/app/main.py backend/tests/test_auth.py
git commit -m "feat: add JWT authentication (register/login)"
```

---

### Task 5: JWT 依赖注入 + 获取当前用户

**Files:**
- Create: `backend/app/middleware/auth_middleware.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/test_middleware.py`

**Interfaces:**
- Consumes: `app.services.auth_service.decode_access_token`
- Produces: `get_current_user` — FastAPI 依赖，从 JWT 解析当前用户；`get_current_tenant` — FastAPI 依赖，返回当前租户

- [ ] **Step 1: 写中间件测试**

```python
# backend/tests/test_middleware.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestAuthMiddleware:
    @pytest.fixture
    def token(self):
        """先注册获取 token"""
        resp = client.post("/api/auth/register", json={
            "tenant_name": "Middleware测试",
            "email": "middleware@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    def test_me_with_valid_token(self, token):
        """验证有效 token 可访问 /me"""
        response = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200
        data = response.json()
        assert "email" in data
        assert data["email"] == "middleware@test.com"

    def test_me_without_token(self):
        """验证无 token 返回 401"""
        response = client.get("/api/auth/me")
        assert response.status_code == 401

    def test_me_with_invalid_token(self):
        """验证无效 token 返回 401"""
        response = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
```

- [ ] **Step 2: 运行测试 → 预期失败**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_middleware.py -v
```
Expected: 404 — `/api/auth/me` 端点不存在

- [ ] **Step 3: 实现 JWT 依赖注入**

```python
# backend/app/middleware/auth_middleware.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.tenant import Tenant
from app.services.auth_service import decode_access_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """从 JWT 解析当前用户"""
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(status_code=401, detail="无效的 token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="token 中缺少用户信息")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="用户已禁用")

    return user

async def get_current_tenant(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """从当前用户获取租户"""
    result = await db.execute(select(Tenant).where(Tenant.id == current_user.tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=404, detail="租户不存在")
    return tenant
```

- [ ] **Step 4: 添加 /me 端点到 auth.py**

```python
# 在 backend/app/api/auth.py 中添加
from app.middleware.auth_middleware import get_current_user
from app.schemas.auth import UserInfo

@router.get("/me", response_model=UserInfo)
async def get_me(current_user: User = Depends(get_current_user)):
    """获取当前用户信息"""
    return UserInfo(
        id=str(current_user.id),
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        tenant_id=str(current_user.tenant_id)
    )
```

- [ ] **Step 5: 运行测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_middleware.py -v
```
Expected: PASS

- [ ] **Step 6: 提交**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/middleware/ backend/app/api/auth.py backend/tests/test_middleware.py
git commit -m "feat: add JWT dependency injection and current user endpoint"
```

---

### Task 6: 多租户数据隔离中间件

**Files:**
- Create: `backend/app/middleware/tenant_middleware.py`
- Modify: `backend/app/main.py` (注册中间件)
- Create: `backend/tests/test_tenant_isolation.py`

**Interfaces:**
- Consumes: `app.middleware.auth_middleware.get_current_tenant`
- Produces: `TenantContext` — 请求级租户上下文，确保所有 DB 查询自动带 `tenant_id` 过滤

- [ ] **Step 1: 写多租户隔离测试**

```python
# backend/tests/test_tenant_isolation.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestTenantIsolation:
    @pytest.fixture
    def tenant_a_token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "租户A",
            "email": "a@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    @pytest.fixture
    def tenant_b_token(self):
        resp = client.post("/api/auth/register", json={
            "tenant_name": "租户B",
            "email": "b@test.com",
            "password": "Test123!@#"
        })
        return resp.json()["access_token"]

    def test_tenant_a_me_has_tenant_a_id(self, tenant_a_token):
        """验证租户A 的用户可以看到自己的 tenant_id"""
        resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_a_token}"})
        tenant_id_a = resp.json()["tenant_id"]
        assert tenant_id_a is not None

    def test_different_tenants_have_different_ids(self, tenant_a_token, tenant_b_token):
        """验证不同租户有不同的 tenant_id"""
        resp_a = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_a_token}"})
        resp_b = client.get("/api/auth/me", headers={"Authorization": f"Bearer {tenant_b_token}"})
        assert resp_a.json()["tenant_id"] != resp_b.json()["tenant_id"]
```

- [ ] **Step 2: 运行测试 → 预期通过（依赖注入已经在上一任务实现）**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/test_tenant_isolation.py -v
```
Expected: PASS

- [ ] **Step 3: 创建租户上下文工具（为后续自动过滤做准备）**

```python
# backend/app/middleware/tenant_middleware.py
from contextvars import ContextVar
from uuid import UUID
from app.models.tenant import Tenant

# 请求级别的租户上下文
current_tenant_id: ContextVar[UUID] = ContextVar("current_tenant_id", default=None)

def set_tenant_context(tenant: Tenant):
    """设置当前请求的租户上下文"""
    current_tenant_id.set(tenant.id)

def get_tenant_context() -> UUID:
    """获取当前请求的租户 ID"""
    return current_tenant_id.get()
```

- [ ] **Step 4: 在 auth.py 的 get_me 中验证隔离**

把 `get_current_user` 修改为自动设置租户上下文，这样后续的所有 API 都可以通过 `get_tenant_context()` 获取当前租户。

```python
# 修改 backend/app/middleware/auth_middleware.py
from app.middleware.tenant_middleware import set_tenant_context

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    # ... 同前 ...
    
    # 设置租户上下文
    set_tenant_context(user.tenant)
    
    return user
```

- [ ] **Step 5: 运行全部测试 → 预期通过**

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/ -v
```
Expected: All PASS

- [ ] **Step 6: 提交**

```bash
cd /d/AI/opc/jwworkflow
git add backend/app/middleware/tenant_middleware.py backend/app/middleware/auth_middleware.py backend/tests/test_tenant_isolation.py
git commit -m "feat: add multi-tenant context isolation"
```

---

### Task 7: Docker Compose 一键启动

**Files:**
- Create: `docker-compose.yml`
- Create: `backend/Dockerfile`
- Create: `frontend/package.json`
- Create: `frontend/Dockerfile`
- Create: `frontend/public/index.html`
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/main.tsx`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`

**Interfaces:**
- Consumes: 所有前面任务的产出
- Produces: 完整的本地开发环境（`docker-compose up` 即可启动）

- [ ] **Step 1: 写 Docker Compose 配置**

```yaml
# docker-compose.yml
version: "3.8"

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: jwworkflow
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 5s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql+psycopg2://postgres:postgres@postgres:5432/jwworkflow
      JWT_SECRET: dev-secret-do-not-use-in-production
      DEBUG: "true"
    volumes:
      - ./backend:/app
      - data:/app/data
    depends_on:
      postgres:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
    depends_on:
      - backend
    command: npm run dev -- --host 0.0.0.0

volumes:
  pgdata:
  data:
```

- [ ] **Step 2: 创建后端 Dockerfile**

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: 创建前端 Vite + React 骨架**

```json
# frontend/package.json
{
  "name": "jwworkflow-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "antd": "^5.20.0",
    "react-router-dom": "^6.26.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.4.0"
  }
}
```

```tsx
# frontend/src/App.tsx
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
```

```tsx
# frontend/src/main.tsx
import React from "react"
import ReactDOM from "react-dom/client"
import App from "./App"

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
```

```html
# frontend/public/index.html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>jwworkflow</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

```ts
# frontend/vite.config.ts
import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": "http://backend:8000"
    }
  }
})
```

```json
# frontend/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true
  },
  "include": ["src"]
}
```

```dockerfile
# frontend/Dockerfile
FROM node:20-slim

WORKDIR /app

COPY package.json .
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

- [ ] **Step 4: 创建 env 文件**

```bash
cd /d/AI/opc/jwworkflow
cp backend/.env.example backend/.env
```

- [ ] **Step 5: 验证 Docker Compose 配置**

```bash
cd /d/AI/opc/jwworkflow
docker compose config
```
Expected: 输出解析后的 Compose 配置（无报错）

- [ ] **Step 6: 提交**

```bash
cd /d/AI/opc/jwworkflow
git add docker-compose.yml backend/Dockerfile frontend/ backend/.env.example
git commit -m "chore: add Docker Compose one-click startup"
```

---

## Phase 1 完整测试清单

运行所有测试验证 Phase 1 完整性：

```bash
cd /d/AI/opc/jwworkflow/backend
JWT_SECRET=test-secret pytest tests/ -v --cov=app --cov-report=term-missing
```

**预期覆盖：**
- `test_config.py` — 配置加载
- `test_database.py` — 数据库连接
- `test_models.py` — ORM 模型
- `test_auth.py` — 注册/登录
- `test_middleware.py` — JWT 依赖注入
- `test_tenant_isolation.py` — 多租户隔离

**覆盖率目标：** ≥ 80%

---

## 后续 Phase 预览

| Phase | 主题 | 依赖 |
|-------|------|------|
| Phase 2 | 工作流引擎核心（DAG/节点注册表/同步执行/SSE） | Phase 1 数据库 |
| Phase 3 | 前端画布（React Flow / 拖拽 / 节点配置） | Phase 1 前端骨架 |
| Phase 4 | 完整执行闭环（画布→执行→结果/控制流+数据处理节点） | Phase 2+3 |
| Phase 5 | 知识库+RAG（文档上传/分块/嵌入/pgvector检索） | Phase 1 数据库 |
| Phase 6 | Agent+场景接入（Agent节点/已有智能体适配/Chatflow） | Phase 4 执行引擎 |
