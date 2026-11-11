# Python + FastAPI + Docker 文章管理系统开发计划

## 一、项目概述

Python

FastAPI

MySQL

SQLAlchemy

Docker

项目名称： Article Management API（文章管理系统）

项目目标： 使用 Python + FastAPI 开发一个完整的文章管理后端，实现文章的新增、查询、修改、删除（CRUD），使用 MySQL 持久化数据，最终通过 Docker Compose 完成容器化部署。

项目以学习 Python 后端开发为基础，同时按照企业实际开发规范组织代码，便于后续扩展用户认证、文章分类、Redis 缓存等功能。

### 核心目标

- 功能开发： 实现文章 CRUD、分页查询、关键词搜索、状态筛选。
- 数据库操作： 使用 SQLAlchemy 2.x 操作 MySQL，使用 Alembic 管理数据库迁移。
- 接口规范： 使用 Pydantic 进行参数校验，统一响应结构与异常处理。
- 工程建设： 分层架构、环境变量配置、日志管理、自动化测试。
- 容器部署： 使用 Dockerfile 构建应用镜像，Docker Compose 启动 API 和 MySQL。

## 二、技术选型

| 技术             | 作用       | 选型说明                   |
| -------------- | -------- | ---------------------- |
| Python 3.12+   | 开发语言     | 学习 Python 类型注解、异步编程    |
| FastAPI        | Web 框架   | 自动生成 OpenAPI 文档，支持异步接口 |
| Uvicorn        | ASGI 服务器 | 运行 FastAPI 应用          |
| MySQL 8.4      | 关系型数据库   | 持久化存储文章数据              |
| SQLAlchemy 2.x | ORM      | 映射 Python 对象与数据库表      |
| Pydantic v2    | 数据校验     | 请求参数及响应数据序列化           |
| Alembic        | 数据库迁移    | 管理数据库表结构版本             |
| Docker         | 容器化      | 构建独立运行环境               |
| Docker Compose | 容器编排     | 管理 API、MySQL 服务        |
| Pytest + HTTPX | 自动化测试    | 测试接口、业务逻辑及异常场景         |

## 三、系统架构设计

采用 Router → Service → Repository → Database 分层架构，避免将所有业务逻辑集中在接口文件中。

客户端 / Swagger UI

HTTP 请求 · JSON 响应

Router 接口层

路由定义、参数校验、状态码

Service 业务层

业务规则、异常处理、事务协调

Repository 数据访问层

SQLAlchemy ORM · CRUD

MySQL 数据库

文章持久化存储

Docker Compose 统一管理应用容器与数据库容器

### 各层职责

| 分层         | 核心职责                       |
| ---------- | -------------------------- |
| Router     | 接收 HTTP 请求、校验参数、调用 Service |
| Schema     | 定义新增、修改、查询及响应数据结构          |
| Service    | 处理文章业务逻辑，判断文章是否存在          |
| Repository | 封装数据库查询与写入                 |
| Model      | 定义 SQLAlchemy 数据库模型        |
| Core       | 数据库连接、配置、日志、公共异常           |

## 四、功能需求

### 4.1 核心 CRUD 接口

| 功能   | 请求方法     | 接口地址                    |
| ---- | -------- | ----------------------- |
| 新增文章 | `POST`   | `/api/v1/articles`      |
| 文章列表 | `GET`    | `/api/v1/articles`      |
| 文章详情 | `GET`    | `/api/v1/articles/{id}` |
| 修改文章 | `PUT`    | `/api/v1/articles/{id}` |
| 部分修改 | `PATCH`  | `/api/v1/articles/{id}` |
| 删除文章 | `DELETE` | `/api/v1/articles/{id}` |
| 健康检查 | `GET`    | `/health`               |

### 4.2 扩展查询功能

文章列表支持以下查询参数：

- `page`：当前页，默认 1。
- `page_size`：每页数量，默认 10，最大 100。
- `keyword`：按照文章标题模糊搜索。
- `status`：按照草稿、已发布状态筛选。
- `sort`：按创建时间或更新时间排序，使用预定义排序字段。

例如：

```
GET /api/v1/articles?page=1&page_size=10&keyword=Python&status=published
```

### 4.3 业务规则

1. 新增文章必须提供标题和正文，默认状态为草稿。
2. 查询不存在的文章返回 HTTP 404。
3. 修改文章时验证字段合法性，更新时间自动更新。
4. 第一版使用物理删除，删除成功返回 HTTP 204。
5. 分页查询返回文章列表、总记录数、当前页及每页数量。
6. 数据库写入异常时进行事务回滚，避免不完整数据。

## 五、数据库设计

第一版只设计 `articles` 一张业务表，减少学习成本。

| 字段         | 数据类型         | 说明                |
| ---------- | ------------ | ----------------- |
| id         | BIGINT       | 主键，自增             |
| title      | VARCHAR(200) | 文章标题，必填           |
| content    | TEXT         | 文章正文，必填           |
| summary    | VARCHAR(500) | 文章摘要，可选           |
| status     | VARCHAR(20)  | draft / published |
| created_at | DATETIME     | 创建时间              |
| updated_at | DATETIME     | 更新时间              |

建议为 `status` 和 `created_at` 建立适当索引。时间统一使用 UTC 保存，在展示时按需要转换时区。

### SQLAlchemy 模型示例

```
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), default="draft", index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )
```

## 六、项目目录结构

```
article-management/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI 入口
│   ├── api/
│   │   └── v1/
│   │       ├── router.py        # 路由聚合
│   │       └── articles.py      # 文章接口
│   ├── core/
│   │   ├── config.py            # 环境配置
│   │   ├── database.py          # 数据库连接
│   │   ├── exceptions.py        # 异常处理
│   │   └── logging.py           # 日志配置
│   ├── models/
│   │   └── article.py           # ORM 模型
│   ├── schemas/
│   │   └── article.py           # Pydantic 模型
│   ├── services/
│   │   └── article_service.py   # 业务层
│   └── repositories/
│       └── article_repository.py # 数据访问层
├── alembic/
│   └── versions/                # 数据库迁移文件
├── tests/
│   ├── conftest.py
│   └── test_articles.py
├── alembic.ini
├── Dockerfile
├── compose.yaml
├── .dockerignore
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## 七、Docker 容器化方案

采用两个容器，通过 Docker Compose 管理：

FastAPI

应用容器

8000 端口

MySQL

数据库容器

3306 端口

### 7.1 Dockerfile

```
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir \
    -r requirements.txt

COPY ./app ./app
COPY ./alembic ./alembic
COPY alembic.ini .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000"]
```

### 7.2 Docker Compose

```
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      mysql:
        condition: service_healthy
    restart: unless-stopped

  mysql:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: articles_db
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test:
        - CMD-SHELL
        - mysqladmin ping -h localhost
          -u root -p"$$MYSQL_ROOT_PASSWORD"
      interval: 10s
      timeout: 5s
      retries: 10
    restart: unless-stopped

volumes:
  mysql_data:
```

应用数据库连接地址使用容器服务名 `mysql`，不要使用 `localhost`。敏感配置放入 `.env`，并将 `.env` 加入 `.gitignore`。

数据库迁移通过 Alembic 单独执行，例如：

```
docker compose run --rm api alembic upgrade head
```

然后启动服务：

```
docker compose up -d --build
```

接口文档：

`http://localhost:8000/docs`

## 八、开发实施计划

建议分为 6 个阶段，预计 7～10 天完成。以下是面向有基础编程经验、正在学习 Python 后端开发的安排。

开发进度规划

10 天计划

第 1 天

项目初始化

Python 环境、FastAPI 启动、项目目录、Git

第 2～3 天

数据库建设

MySQL、SQLAlchemy、Pydantic、Alembic

第 4～5 天

CRUD 接口开发

新增、详情、列表、修改、删除

第 6～7 天

业务功能完善

分页筛选、统一异常、日志、参数校验

第 8～9 天

Docker 与测试

Dockerfile、Compose、Pytest、接口联调

第 10 天

验收与文档

README、接口文档、部署验证

### 每阶段验收标准

| 阶段       | 验收成果                    |
| -------- | ----------------------- |
| 1. 初始化   | FastAPI 可启动，`/docs` 可访问 |
| 2. 数据库   | MySQL 连接正常，Alembic 可建表  |
| 3. CRUD  | 五项核心操作全部正常              |
| 4. 业务完善  | 分页、搜索、异常处理正常            |
| 5. 容器与测试 | Docker 一键启动，自动化测试通过     |
| 6. 最终验收  | 完整 README，可从零部署项目       |

## 九、测试方案

使用 Pytest + HTTPX 编写接口测试，测试数据库与实际业务数据库隔离。

| 测试场景        | 预期结果             |
| ----------- | ---------------- |
| 新增合法文章      | HTTP 201，返回文章 ID |
| 新增缺少标题      | HTTP 422         |
| 查询已存在文章     | HTTP 200，内容正确    |
| 查询不存在的文章    | HTTP 404         |
| 更新文章内容      | HTTP 200，数据库同步更新 |
| 部分更新文章      | 仅修改提交的字段         |
| 删除已存在文章     | HTTP 204         |
| 删除不存在的文章    | HTTP 404         |
| 分页查询        | 记录数量、总数正确        |
| 关键词搜索       | 返回符合条件的文章        |
| 重启 MySQL 容器 | 数据卷中的文章仍然存在      |

## 十、最终交付成果

完成后，项目应具备：

- 可运行的 FastAPI 文章管理后端。
- MySQL 数据库及 Alembic 迁移文件。
- 完整的文章 CRUD RESTful API。
- 自动生成的 Swagger 接口文档。
- Dockerfile 和 Docker Compose 配置。
- 自动化测试用例。
- README 项目说明、环境配置及部署指南。

## 十一、后续扩展方向

核心功能验收后，可按实际业务项目的方向迭代：

| 优先级 | 功能       | 学习重点               |
| --- | -------- | ------------------ |
| P1  | JWT 用户登录 | 身份认证、权限控制          |
| P1  | 文章分类和标签  | 数据库表关系             |
| P2  | Redis 缓存 | 缓存设计及失效策略          |
| P2  | 异步任务     | asyncio、后台任务       |
| P2  | CI/CD    | 自动测试、镜像构建、部署       |
| P3  | AI 文章摘要  | 大模型 API 调用         |
| P3  | RAG 文章问答 | Embedding、向量检索、RAG |

建议开发顺序： 先完成单表 CRUD，再完成数据库迁移与 Docker 部署，最后完善测试和工程规范。不要在第一阶段引入 Redis、消息队列或复杂微服务架构，优先建立一套真正能够运行、测试和部署的 FastAPI 项目。

后续学习 AI、Agent、RAG 时，可以直接在这个项目上增加文章向量化、语义检索和智能问答功能，逐步演进为一个 AI 知识库后端。