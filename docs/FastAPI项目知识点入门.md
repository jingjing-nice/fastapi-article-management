# 从文章管理项目入门 FastAPI

> 面向第一次学习后端的读者，按本项目实际源码整理。阅读顺序：先理解请求如何流转，再学习参数、数据库和登录。文档描述的是当前代码，已知问题见最后一节。

## 1. 这个项目到底做什么

你可以把它想象成一个文章管理后台的“服务窗口”。浏览器或前端发送请求，后端检查参数和身份，访问数据库，再把结果返回。

```text
前端 → HTTP 请求 → FastAPI 路由 → Service 业务处理 → Repository 数据访问
                                                        ↓
                                                   PostgreSQL
前端 ← JSON 响应 ← 响应模型 ← 返回处理结果 ←─────────────────┘
```

例如新增文章：前端提交标题和正文，后端识别登录用户，保存文章，把文章 ID 和内容返回。

几个基础词：

| 名词 | 通俗解释 | 项目里的例子 |
|---|---|---|
| API / 接口 | 程序提供的服务入口 | 新增文章接口 |
| HTTP | 客户端和服务器交流的规则 | GET、POST 请求 |
| URL | 请求的地址 | `/api/v1/articles` |
| JSON | 用键和值组织数据的格式 | `{"name": "Python 入门"}` |
| 数据库 | 长期保存信息的地方 | PostgreSQL |
| ORM | 用 Python 对象操作数据库的工具 | SQLModel |
| Token | 登录后获得、后续请求携带的凭证 | JWT access token |

## 2. 各个工具负责什么

| 工具 | 作用 |
|---|---|
| FastAPI | 注册接口、解析请求、组织校验和响应 |
| Uvicorn | 启动服务器，把网络请求交给 FastAPI |
| Pydantic | 根据类型和规则检查数据 |
| SQLModel | 定义数据模型，结合 SQLAlchemy 操作数据库 |
| psycopg | Python 连接 PostgreSQL 的驱动 |
| Alembic | 记录和执行数据库表结构变更 |
| pydantic-settings | 从环境变量和 `.env` 读取配置 |
| PyJWT / pwdlib | 签发验证令牌、哈希和校验密码 |
| pytest / httpx | 测试接口和业务行为 |
| uv | 管理依赖、运行项目命令 |

这些工具是配合使用的。数据库迁移、JWT、Docker 并不是 FastAPI 自动完成的功能。

## 3. 先看懂项目目录

```text
app/
├── main.py                     # 应用入口，注册路由、中间件和异常处理
├── v1/
│   ├── articles.py             # 文章接口
│   └── auth.py                 # 注册、登录、当前用户接口
├── schemas/                    # 接收什么数据、返回什么数据
├── models/                     # 数据库表映射
├── services/                   # 业务规则和事务
├── repositories/               # 文章数据库查询和写入
└── core/
    ├── config.py               # 配置
    ├── database.py             # 数据库引擎与会话
    ├── auth.py                 # 获取当前用户、权限依赖
    ├── security.py             # 密码和 JWT
    ├── exceptions.py           # 统一数据库异常响应
    └── logging.py              # 日志
alembic/                        # 数据库迁移
 tests/                         # 自动化测试
```

分层的目的：接口负责接待请求，业务层决定怎么办，数据层负责取存数据。项目用户服务直接查询数据库，说明分层是组织方法，不是 FastAPI 强制规定。

## 4. FastAPI 如何创建接口

源码：`app/main.py`。

```python
app = FastAPI(title=get_settings().app_name, version="0.1.0")

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
```

- `FastAPI(...)` 创建应用。
- `@app.get(...)` 把一个地址和 Python 函数绑定。
- 请求 `GET /health` 时执行 `health()`。
- 返回的字典会被转换成 JSON。
- `-> dict[str, str]` 是返回值的类型提示。

启动命令中的 `app.main:app` 表示：加载 `app/main.py` 文件中名为 `app` 的对象。

```bash
uv run uvicorn app.main:app --reload
```

`--reload` 用于开发时监听代码变化，不适合作为生产部署配置。

## 5. APIRouter：把接口按功能分组

源码：`app/v1/articles.py`。

```python
router = APIRouter(
    prefix="/api/v1/articles",
    tags=["文章"],
    dependencies=[Depends(get_current_user)],
)
```

`prefix` 是公共路径前缀，`tags` 用于文档分组，`dependencies` 表示这个路由组先执行登录校验。

在 `main.py` 中通过 `app.include_router(articles_router)` 接入主应用。

| 方法 | 路径 | 用途 |
|---|---|---|
| POST | `/api/v1/auth/register` | 注册，JSON 请求体 |
| POST | `/api/v1/auth/login` | 登录，表单请求体 |
| GET | `/api/v1/auth/me` | 查看当前用户 |
| POST | `/api/v1/articles` | 新增文章 |
| GET | `/api/v1/articles` | 文章列表 |
| GET | `/api/v1/articles/{article_id}` | 文章详情，当前实现有问题 |
| PUT / PATCH | `/api/v1/articles/{article_id}` | 更新，当前查询链有问题 |
| DELETE | `/api/v1/articles/{article_id}` | 删除，当前查询链有问题 |
| GET | `/health` | 应用存活检查 |

CRUD 就是新增（Create）、查询（Read）、修改（Update）、删除（Delete）。

## 6. 参数从哪里来

### 6.1 路径参数：要操作哪一条

```python
@router.get("/{article_id}")
def get_article_by_id(article_id: int, ...):
    ...
```

请求 `/api/v1/articles/12`，`article_id` 就是整数 `12`。传入不能转换为整数的值会触发参数校验错误。

### 6.2 查询参数：怎么查询

```text
/api/v1/articles?page=2&page_size=10&status=draft
```

项目写法：

```python
page: Annotated[int, Query(ge=1)] = 1
page_size: Annotated[int, Query(ge=1, le=100)] = 10
```

`Annotated` 可以理解成“类型加补充说明”；`ge` 是大于等于，`le` 是小于等于。不传时使用默认值，超出范围通常返回 422。

项目用 `Query(alias="status")`，让 Python 内部参数名为 `article_status`，对外仍使用 `status`。

### 6.3 请求体：提交完整的数据对象

源码：`app/schemas/article.py`。

```python
class ArticleCreate(SQLModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    status: Literal["draft", "published"] = "draft"
```

对应 JSON：

```json
{
  "name": "第一篇文章",
  "content": "开始学习 FastAPI",
  "summary": null,
  "status": "draft"
}
```

- `name`、`content` 没有默认值，必须提交。
- `str | None` 表示允许字符串或空值；有默认值才表示可以省略。
- `Literal` 限定可选值。
- `extra="forbid"` 拒绝模型之外的字段。
- 长度至少为 1 不代表自动去除空格，纯空格字符串需要额外校验。

用户注册的 `field_validator(..., mode="before")` 会先把用户名去除首尾空格并转为小写，再做字段校验。

## 7. 请求模型、表模型、响应模型有什么区别

| 类型 | 项目示例 | 回答的问题 |
|---|---|---|
| 请求模型 | `ArticleCreate`、`ArticleUpdate` | 前端能提交什么？ |
| 表模型 | `Article(..., table=True)` | 数据库保存什么？ |
| 响应模型 | `ArticlePublic`、`UserPublic` | 前端能看到什么？ |

`table=True` 声明表映射；只声明模型不会自动修改真实数据库。

```python
@router.post("", response_model=ArticlePublic, status_code=201)
```

`response_model` 用于校验、序列化并限定响应结构。比如 `UserPublic` 不声明 `password_hash`，因此不会把密码哈希作为正常响应字段返回。

输入校验失败通常是 422；服务器返回的数据不符合响应模型属于服务端问题，不能混为一谈。

## 8. Depends：由框架准备需要的东西

源码：`app/core/database.py`。

```python
def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
```

接口声明 `session: SessionDep` 后，FastAPI 会调用依赖函数，把会话交给接口，在依赖退出时关闭会话。

可以把依赖注入理解为：“我声明需要数据库会话，框架负责准备和交付。”`yield` 把资源使用阶段和退出清理阶段分开。关闭会话不等于自动提交，项目业务层仍明确调用 `commit()`。

同理：

```python
CurrentUserDep = Annotated[Users, Depends(get_current_user)]
```

接口通过 `current_user: CurrentUserDep` 获取已经验证的用户。同一次请求中，相同依赖默认会被缓存，因此路由组和参数重复声明登录依赖通常不会重复执行整套认证。

## 9. 一次新增文章怎样进入数据库

对应 `articles.py` → `article_service.py` → `article_repository.py`。

1. 路由验证登录和 `ArticleCreate`。
2. 业务层把请求模型转换成 `Article`，由服务器写入当前用户的 `owner_id`。
3. 数据层执行 `add()` 和 `flush()`。
4. 业务层 `commit()` 提交事务。
5. `refresh()` 读取数据库中的字段，按 `ArticlePublic` 返回。

| 操作 | 通俗解释 |
|---|---|
| `add()` | 把对象加入待保存会话 |
| `flush()` | 把待执行变更发送到数据库，但尚未最终提交 |
| `commit()` | 提交当前事务 |
| `rollback()` | 放弃当前失败事务中的变更 |
| `refresh()` | 从数据库重新加载对象字段 |

事务就像一次打包操作：成功一起提交，失败回滚。代码捕获数据库异常后要重新 `raise`，让异常处理器接管，不能假装保存成功。

## 10. 列表的分页、筛选与排序

源码：`app/repositories/article_repository.py`。

```python
offset = (page - 1) * page_size
```

每页 10 条时，第 1 页跳过 0 条，第 2 页跳过 10 条。`offset()` 控制跳过数量，`limit()` 控制返回上限。

列表返回 `total`、`items`、`page`、`page_size`。其中 `total` 是符合筛选条件的总数，不是当前页条数。统计和列表复用筛选条件，避免总数与内容对不上。

- `where()`：筛选记录，包括所属用户、标题和状态。
- `contains(name, autoescape=True)`：标题包含关键词，并转义 LIKE 通配符。
- `order_by()`：控制排序。
- `-created_at`：按创建时间降序。
- 相同时间再按 ID 排序，让分页结果更稳定。

## 11. 部分更新：没传与传 null 不一样

项目使用：

```python
changes = data.model_dump(exclude_unset=True)
```

| 请求 | 意义 |
|---|---|
| `{}` | 什么都不改 |
| `{"name": "新标题"}` | 只改标题 |
| `{"summary": null}` | 清空摘要 |
| `{"name": null}` | 业务层拒绝，返回 422 |

`exclude_unset=True` 只提取实际提交的字段，保留显式提交的 `null`。如果误用 `exclude_none=True`，就无法通过 `null` 清空摘要。

本项目 PUT 和 PATCH 都按部分更新处理。学习时应记住这是本项目的接口约定；PUT 常用于完整替换，PATCH 常用于部分修改。

## 12. 注册、登录与权限

### 注册

JSON 用户信息 → 规范化用户名 → 检查重名 → 密码哈希 → 保存用户。

哈希不是可解密保存的密码。登录时用密码验证函数检查输入与哈希是否匹配。注册模型不接收角色，服务端固定创建普通用户。

### 登录

本项目使用 `OAuth2PasswordRequestForm`，因此登录提交的是表单，不能照搬注册接口的 JSON 格式。

验证成功后返回：

```json
{"access_token": "令牌字符串", "token_type": "bearer", "expires_in": 1800}
```

默认有效期 30 分钟，实际由配置决定。

### 携带令牌

```http
Authorization: Bearer 你的access_token
```

`OAuth2PasswordBearer` 提取令牌；`get_current_user` 验证签名、必要字段和有效期，再查询用户是否存在且启用。

JWT 里 `sub` 是用户 ID，`iat` 是签发时间，`exp` 是到期时间。签名保证内容不能被随意篡改，不表示内容加密，不应把密码放进去。

### 身份与权限

认证回答“你是谁”，授权回答“你能做什么”。代码意图是普通用户只操作自己的文章，管理员可跨用户操作。管理员角色来自数据库。

`require_admin` 已定义，但文章路由没有用它作为管理员专属门槛；文章接口通过角色判断设置所属用户过滤。当前详情及更新、删除链存在实现缺口，见第 18 节。

## 13. 状态码和异常

| 状态码 | 项目中的含义 |
|---|---|
| 200 | 查询、更新成功；当前注册和登录也默认返回 200 |
| 201 | 新增文章成功 |
| 204 | 删除成功，没有响应体 |
| 400 | 用户名已存在 |
| 401 | 未登录、令牌失效或登录失败 |
| 403 | 需要管理员权限，适用于调用 `require_admin` 的场景 |
| 404 | 文章不存在或对当前用户不可见 |
| 422 | 请求参数或业务字段不符合要求 |
| 500 | 服务端内部错误，如数据库操作异常 |

业务异常通过 `raise HTTPException(...)` 返回。数据库异常由主应用注册的处理器记录日志，并向客户端返回通用错误信息。

## 14. 同步 def 与异步 async def

大部分路由使用 `def`，数据库也使用同步 `Session`，这是一套同步数据库访问方式。FastAPI 会在线程池中执行普通同步路由及同步依赖。

`async def` 适合搭配可以 `await` 的异步操作，不是加上就自动提速。本项目 `get_current_user` 虽然是异步函数，里面的 `session.get()` 仍是同步数据库操作，可能阻塞事件循环；进一步优化时应统一考虑依赖和数据库访问方式。

## 15. 配置、跨域与健康检查

`Settings` 从环境变量和 `.env` 读取数据库地址、日志等级及 JWT 配置。`get_settings()` 使用缓存，通常修改配置后需要重启进程。

`JWT_SECRET_KEY` 没有默认值，必须配置。`SecretStr` 能减少直接打印时意外泄露，但不等于加密存储。

CORS 是浏览器的跨域访问规则。项目允许 `localhost:5173` 和 `127.0.0.1:5173` 的前端来源，开放 Authorization 等请求头。跨域配置不能代替登录校验。

`/health` 当前只返回固定结果，能证明应用可以响应，不能证明数据库连接正常。

## 16. 按步骤亲手调用

先准备 Python 3.13、uv 和 PostgreSQL。在项目根目录运行：

```bash
uv sync --locked
```

`.env` 配置示例，替换所有占位值，真实密码和密钥不要提交到仓库：

```dotenv
DB_HOST=127.0.0.1
DB_PORT=5432
DB_USER=articles_db
DB_NAME=article_management
DB_PASSWORD=你的数据库密码
JWT_SECRET_KEY=替换为足够长且随机的密钥
```

空数据库执行迁移，已有业务表时先核对迁移状态和表结构：

```bash
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

打开 `http://127.0.0.1:8000/docs` 查看交互文档。也可以在本地终端执行：

```bash
# 1. 注册；重复执行相同用户名会提示已存在
curl -X POST http://127.0.0.1:8000/api/v1/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"username":"beginner","password":"example-pass-123"}'

# 2. 登录：注意这里是表单
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  --data-urlencode 'username=beginner' \
  --data-urlencode 'password=example-pass-123'

# 3. 将返回的 access_token 替换到下面占位文字
curl -X POST http://127.0.0.1:8000/api/v1/articles \
  -H 'Authorization: Bearer 替换为access_token' \
  -H 'Content-Type: application/json' \
  -d '{"name":"我的第一篇文章","content":"你好 FastAPI"}'

# 4. 查询列表
curl 'http://127.0.0.1:8000/api/v1/articles?page=1&page_size=10' \
  -H 'Authorization: Bearer 替换为access_token'
```

Alembic 管表结构，业务接口管表里的数据。修改 Python 模型后仍需编写、检查并执行对应迁移。

## 17. 如何用测试巩固学习

先阅读 `tests/test_api_contract.py`，把测试当成“给接口发请求并检查答案”的例子。可运行：

```bash
uv run python -m pytest tests/test_api_contract.py -q
```

按 README，这组测试使用内存 SQLite，不修改业务数据库。PostgreSQL 集成测试需要单独配置 `TEST_DATABASE_URL`，测试库名以 `_test` 结尾。不要拿业务数据库当测试库。

建议练习顺序：健康检查 → 注册登录 → 新增和列表 → 参数错误 → 用户隔离 → 更新和删除。观察状态码、响应 JSON 和数据库变化三者是否一致。

## 18. 当前代码里需要特别注意的问题

以下是阅读源码发现的问题，本次仅生成学习文档，没有修改业务代码，也没有执行接口测试。

1. **详情接口传参与 Service 签名不匹配。** `app/v1/articles.py` 调用 `article_service.get_article_by_id(..., owner_id=...)`，但 Service 的同名函数只接受 `article_id` 和 `session`，会产生 `TypeError`。
2. **Service 调用了不存在的数据层函数。** `app/services/article_service.py` 的 `get_article_by_id` 调用 `article_repository.get_visible_article`，但 Repository 实际提供的是 `get_article_by_id`，会产生 `AttributeError`。更新和删除也依赖这条查询链，因此受影响。
3. **权限设计不能当成已验证可用。** 查询链修复时，要让详情、更新、删除统一经过所属用户检查，同时保留管理员跨用户访问规则，并测试普通用户访问他人文章返回 404。
4. **已有 README 未完整体现登录要求。** 当前文章路由统一要求登录，本学习文档示例已包含 Bearer Token；启动配置也补充了必需的 JWT 密钥。

学习时应区分“框架的用法”“项目期望的业务规则”和“当前代码实际能否正确执行”。

## 19. 复习清单

- 能说明一个请求从路由到数据库再返回的过程。
- 能区分路径参数、查询参数、JSON 请求体和登录表单。
- 能解释请求模型、数据库模型和响应模型。
- 知道 Depends 如何提供会话和当前用户。
- 知道 flush 不等于 commit，失败时为什么 rollback。
- 能解释不传字段与显式传 null 的差别。
- 能区分身份认证、角色权限和数据所属用户过滤。
- 知道 JWT 不等于加密，CORS 不等于身份认证。
- 知道修改模型后需要数据库迁移。

推荐读代码顺序：`main.py` → `v1/articles.py` → `schemas/article.py` → `core/database.py` → `services/article_service.py` → `repositories/article_repository.py` → 注册登录相关文件 → 测试。
