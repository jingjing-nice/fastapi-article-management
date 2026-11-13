# 文章管理系统

基于 Python 3.13、FastAPI、SQLModel 和 PostgreSQL 的文章管理 API。

支持文章新增、详情查询、分页列表、关键词搜索、状态筛选、
时间排序、部分更新和物理删除。

## 本地启动

安装 uv 和 Python 3.13，准备 PostgreSQL 数据库。

安装依赖：

```bash
uv sync --locked
```

在项目根目录配置 `.env`：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=articles_db
DB_NAME=article_management
DB_PASSWORD=你的数据库密码
```

对空数据库执行迁移：

```bash
uv run alembic upgrade head
```

已有业务表的数据库需要先核对结构，不要直接重复建表。

启动服务：

```bash
uv run uvicorn app.main:app --reload
```

接口文档：http://127.0.0.1:8000/docs

健康检查：http://127.0.0.1:8000/health



## Docker 部署

安装并启动 Docker Desktop，在项目根目录的 `.env` 中配置：

```dotenv
DB_USER=articles_db
DB_NAME=article_management
DB_PASSWORD=请替换为实际密码
```

构建 API 镜像：

```bash
docker compose build api
```

启动数据库：

```bash
docker compose up -d postgres
docker compose ps
```

等待 PostgreSQL 显示 healthy。首次使用空数据库时执行建表迁移：

```bash
docker compose run --rm api alembic upgrade head
```

启动 API：

```bash
docker compose up -d api
```

接口文档：http://127.0.0.1:8000/docs

如果本机 Uvicorn 占用 8000 端口，先停止本机服务。

查看状态与日志：

```bash
docker compose ps
docker compose logs --tail=50 api
```

停止并移除容器，保留数据库数据卷：

```bash
docker compose down
```

数据库数据保存在 postgres_data 卷中。
不要使用 `docker compose down -v`，除非明确需要删除数据库数据。


## 自动化测试

安装开发依赖：

```bash
uv sync --locked
```

运行无需 PostgreSQL 的接口测试：

```bash
uv run python -m pytest tests/test_api_contract.py -q
```

这组测试使用内存 SQLite，不修改业务数据库。

### PostgreSQL 集成测试

创建独立测试库，仅首次执行：

```bash
docker compose exec postgres sh -c 'createdb -U "$POSTGRES_USER" articles_test'
```

确保 Compose 将 PostgreSQL 端口映射为 `127.0.0.1:5433:5432`，
然后在 `.env` 中配置：

```dotenv
TEST_DATABASE_URL=postgresql+psycopg://articles_db:你的数据库密码@127.0.0.1:5433/articles_test
```

用户名和密码必须与容器配置一致；密码中的特殊字符需要 URL 编码。
测试库名必须以 `_test` 结尾，不得使用业务数据库。

运行全部测试：

```bash
uv run python -m pytest -q
```

未配置 `TEST_DATABASE_URL` 时，PostgreSQL 集成测试会跳过。


## 接口说明

| 方法 | 路径 | 功能 |
|---|---|---|
| POST | `/api/v1/articles` | 新增文章 |
| GET | `/api/v1/articles` | 分页查询 |
| GET | `/api/v1/articles/{id}` | 查询详情 |
| PUT / PATCH | `/api/v1/articles/{id}` | 更新提交的字段 |
| DELETE | `/api/v1/articles/{id}` | 物理删除 |
| GET | `/health` | 应用健康检查 |

### 新增文章

```json
{
  "name": "Python 入门",
  "content": "文章正文",
  "summary": "可选摘要",
  "status": "draft"
}
```

标题 name 必填，最长 100 字；正文 content 必填。
摘要 summary 可选，最长 500 字。
状态支持 draft、published，默认 draft。

### 列表参数

- page：默认 1，最小 1。
- page_size：默认 10，范围 1～100。
- name：按标题模糊搜索。
- status：筛选 draft 或 published。
- sort：支持 created_at、-created_at、updated_at、-updated_at。
  前缀 - 表示降序；不传时按 ID 升序。

### 更新与删除

PUT 和 PATCH 均只修改提交的字段。
summary 可传 null 清空；name、content、status 不允许为 null。

新增成功返回 201，查询与更新成功返回 200。
删除成功返回 204，响应体为空。
文章不存在返回 404，参数错误返回 422。





需要。**修改本机代码不会自动更新阿里云上的服务**，需要上传改动并重新构建。

**1. Mac 本地终端上传代码：**

```bash
cd /Users/jingjing/Desktop/python/fastapi-article-management

scp -r app root@114.55.143.126:/opt/article-management/
```

如果修改了依赖，也上传：

```bash
scp pyproject.toml uv.lock root@114.55.143.126:/opt/article-management/
```

**2. 服务器终端重新构建并启动 API：**

```bash
cd /opt/article-management
docker compose build api
docker compose up -d --no-deps api
```

**3. 验证更新：**

```bash
curl -f https://api.jing-aichat.xyz/health
docker compose logs --tail=50 api
```

更新会短暂重启 API，数据库数据卷会保留。**不要执行 `docker compose down -v`。**

如果修改了数据库表结构，还需要编写、上传迁移文件，备份数据库后执行 `alembic upgrade head`；只改 Python 模型不会自动修改表。