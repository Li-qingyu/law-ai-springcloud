# 法律 AI 智能服务平台

**基于 Spring Cloud 微服务、RAG 检索增强生成与 LangGraph 多 Agent 的法律咨询与知识管理平台。**

项目采用 **Vue 3 前端 + Java 微服务 + Python AI 服务**的前后端分离架构，将法律知识浏览、案例检索、智能咨询和后台知识库维护连接起来：用户可以通过自然语言提问，获取带法条与案例参考资料的回答；管理员可以维护法律内容、同步向量知识库，并通过 AI 管理助手执行数据操作；超级管理员进一步管理模型配置、用户权限和 Token 配额。

AI 咨询链路结合 Milvus 混合检索、多路问题改写、Rerank 精排、分层会话记忆与 SSE 流式输出。管理助手以 LangGraph 编排任务，数据管理能力通过内嵌于 Java 服务的 **MCP Server** 提供，并结合工具白名单、用户身份透传和后端 RBAC 授权控制操作边界。

> **使用边界**：本项目用于法律信息查询、知识学习与辅助咨询。AI 回答及引用资料仅供参考，不替代专业律师意见；涉及具体案件时，应核验原始法律文件、时效与适用范围。

## 目录

- [页面展示](#页面展示)
- [核心功能](#核心功能)
- [技术亮点](#技术亮点)
- [系统架构](#系统架构)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [Docker 部署](#docker-部署)
- [相关文档](#相关文档)
- [安全与使用说明](#安全与使用说明)

## 页面展示

以下直接展示 `docs/图片资料/` 中的项目实际页面截图。首页与 AI 法律咨询默认展开，其余页面点击标题即可查看。

### 用户端

#### 平台首页

首页汇集 AI 法律咨询、法典浏览与案例学习入口，通过轮播内容和热门案例帮助用户快速找到需要的法律信息。

![法律咨询平台首页](docs/图片资料/屏幕截图%202026-11-23%20215843.png)

#### AI 法律咨询

对话页面支持历史会话切换、Markdown 回答展示和参考资料卡片；结合 RAG 检索与 SSE 流式输出，为咨询回答提供法条与案例依据。

![AI 法律咨询与参考资料](docs/图片资料/屏幕截图%202026-11-23%20215821.png)

<details>
<summary><strong>法律案例：浏览案例、查看详情与收藏</strong></summary>

案例以卡片形式展示标题、摘要、类型及标签，提供详情查看和收藏入口，配合搜索页面查询相关法律内容。

![法律案例列表](docs/图片资料/屏幕截图%202026-11-23%20215902.png)

</details>

<details>
<summary><strong>法典浏览：查看法律书籍及所属条文</strong></summary>

展示法典名称、发布与生效日期等信息，用户可以进入对应法典继续浏览法律条文。

![法典浏览页面](docs/图片资料/屏幕截图%202026-11-23%20215914.png)

</details>

<details>
<summary><strong>个人中心：案例收藏入口与 Token 用量</strong></summary>

个人中心提供账号信息与密码管理、案例收藏入口，并展示日/月 Token 已用量和配额进度。

![个人中心与 Token 配额使用情况](docs/图片资料/屏幕截图%202026-11-23%20215934.png)

</details>

### 管理端

<details>
<summary><strong>知识库同步：法律条文与案例向量化</strong></summary>

管理员可以按法典同步法律条文，或同步法律案例，将业务数据更新到用于 AI 检索的 Milvus 知识库。

![知识库同步页面](docs/图片资料/屏幕截图%202026-11-23%20220002.png)

</details>

<details>
<summary><strong>AI 配置管理：模型提供商、启停与默认模型</strong></summary>

提供模型配置列表与新增入口，管理提供商、模型名称、API 地址、启用状态和默认模型。

![AI 模型配置管理](docs/图片资料/屏幕截图%202026-11-23%20220016.png)

</details>

<details>
<summary><strong>Token 配额管理：用户日/月额度与使用日志</strong></summary>

集中展示用户的日/月用量、额度和累计消耗，提供配额管理与使用日志入口；具体可执行操作由角色权限决定。

![Token 配额管理页面](docs/图片资料/屏幕截图%202026-11-23%20215944.png)

</details>

<details>
<summary><strong>AI 智能管理助手：自然语言驱动后台操作</strong></summary>

管理助手提供数据、文件、日志和权限管理任务入口。路由工作流按意图和角色分发任务，数据管理 Agent 通过 MCP 工具查询或维护知识库，删除等危险操作需对话确认。

![AI 智能管理助手](docs/图片资料/屏幕截图%202026-11-23%20220029.png)

</details>

## 核心功能

### 用户端

| 功能 | 说明 |
| --- | --- |
| 智能法律咨询 | 支持普通与 SSE 流式对话，结合检索结果生成回答，并返回法条、案例等参考资料卡片。 |
| 会话与历史管理 | 查看、切换和清理咨询会话，保留上下文以支持连续追问。 |
| 分层对话记忆 | 工作记忆保留近期对话，短期记忆以摘要压缩上下文，长期记忆按用户召回跨会话历史。 |
| 法律知识浏览 | 浏览法典及所属条文，查看法律案例、标签、摘要和详情。 |
| 搜索与收藏 | 关键词检索法律内容，收藏案例并在个人中心或收藏页面查看。 |
| 账号与游客体系 | 支持注册、登录、邮箱验证码及游客咨询；注册后迁移合并游客咨询数据。 |
| Token 用量查看 | 展示个人日/月额度及已用量，帮助用户了解 AI 服务使用情况。 |

### 管理端

| 功能 | 说明 |
| --- | --- |
| 法律内容维护 | 管理法律案例、类型、书籍和条文，提供批量导入等内容维护能力。 |
| 知识库同步 | 将法条与案例向量化写入 Milvus，支持同步任务及进度查询。 |
| 工作台与用户管理 | 提供业务数据统计、用户管理等后台入口。 |
| AI 管理助手 | Router 分发数据、文件、日志、权限管理任务；数据管理工作流支持工具调用、参数补充与危险操作确认。 |
| MCP 数据管理工具 | 暴露法条、案例、法典和类型的查询、维护、导入及同步工具，供 Python Agent 调用。 |
| AI 配置管理 | 管理多 Provider 模型配置，通过 Redis、Java 内部接口与环境配置的降级链获取可用配置。 |
| Token 配额治理 | 管理用户日/月额度，记录 Token 使用明细，提供使用统计与定时重置。 |
| 分级角色权限 | 区分 `super_admin`、`admin`、`user`，结合网关鉴权、服务端授权和 Agent 工具预筛选控制权限。 |

> **当前 MCP 范围**：数据管理 Agent 已接入 MCP，Java 侧当前提供 26 个工具。文件、日志、权限 Agent 仍使用原有工具链路，进一步 MCP 化属于后续迭代，不代表所有管理操作都已迁移。

## 技术亮点

### 1. 可组合的 RAG 检索架构

- **策略与管道分离**：向量、混合、多路 Query 改写策略决定如何召回；去重与精排管道负责处理候选结果。
- **Dense + BM25 混合检索**：结合语义匹配与关键词匹配，由 Milvus 服务端进行 RRF 融合。
- **Rerank 精排与降级**：使用 DashScope `gte-rerank-v2` 重排候选内容；精排服务异常时保留候选结果作为降级输出。
- **结构化参考资料**：将检索到的法条、案例等整理为 `data_cards`，方便前端展示和用户核验。

### 2. 分阶段推理与响应优化

- 将问题预分析、Agent 工具推理与最终流式生成分开，减少工具循环重复生成完整回答的开销。
- 通过规则与 LLM 兜底完成意图识别，结合并行检索处理可独立的工具任务。
- 使用 Milvus 语义缓存复用相似问题的回答，配合相似度阈值与 TTL 控制缓存有效性。

### 3. 三级记忆与隐私保护

- **工作记忆**：保留最近若干轮对话，并限制上下文 Token 数。
- **短期记忆**：将较早对话压缩为摘要，减少长会话的上下文膨胀。
- **长期记忆**：通过 `consult_history` 向量集合按用户语义检索历史咨询。
- **隐私脱敏**：提供手机号、身份证号等敏感信息的脱敏机制与开关。

### 4. LangGraph 管理工作流与 MCP 工具接入

- Router 负责意图分类、权限检查与任务路由，子 Agent 负责具体操作，避免在父图中混合执行与确认逻辑。
- 数据管理工作流通过 `interrupt` / `resume` 实现参数追问和删除等危险操作的对话式确认。
- MCP Server 内嵌于 `law-ai-service`，使用无状态 Streamable HTTP，通过 `/mcp` 暴露工具，不额外部署独立 Java 服务。
- Python 通过 `langchain-mcp-adapters` 拉取工具，在绑定给 LLM 前按角色预筛选；Java 工具注册表及下游授权继续校验操作权限。

### 5. 角色权限与模型用量治理

- Java 使用 `@RequireRole` 注解和 AOP 授权，统一控制管理接口的角色访问范围。
- MCP 请求携带用户凭证，服务端校验 JWT 与 Redis 登录会话，并向下游透传用户上下文。
- AI 配置支持多 Provider 与默认模型管理，配置读取采用 **Redis → Java 内部接口 → 环境配置**降级链。
- Token 按日/月管理配额，异步记录使用明细，定时重置周期用量。

### 6. 事件驱动的数据同步

通过 `@TransactionalEventListener(AFTER_COMMIT)` 与 `@Async` 在数据库事务提交后异步同步咨询向量数据，解耦业务落库与 Milvus 写入；法律内容也可通过管理端手动同步更新知识库。

> 上述内容描述代码中的实现机制，不将缺少可复现基准的召回率、Token 节省比例或响应耗时作为性能承诺。实际效果取决于模型、数据规模、部署资源与请求场景。

## 系统架构

后端包含 **5 个 Java 微服务（含网关）+ 1 个 Python AI 服务**，公共模块以依赖包形式复用，不单独作为服务部署。

```text
浏览器 · Vue 3 前端（Web/vue-law）
    │ 开发环境：Vite /api 代理；部署环境：Nginx 反向代理
    ▼
law-gateway · 统一路由 / JWT 鉴权 / 角色访问控制
    │
    ├── law-user-service   · 账号 / 邮箱验证 / 游客数据迁移
    ├── law-law-service    · 法条 / 法典 / 案例 / 类型 / 搜索收藏
    ├── law-common-service · 文件上传 / 轮播图 / 工作台统计
    └── law-ai-service     · 咨询桥接 / 会话 / 配额 / AI 配置 / MCP Server
            │ HTTP / SSE
            ▼
      python-ai-service   · RAG / 分层记忆 / 语义缓存 / LangGraph Agent
            │
            ├── Milvus · 法条、案例、历史咨询与语义缓存检索
            ├── 模型服务 · 通义千问 / DeepSeek 等
            └── MCP · 内网调用 law-ai-service:8083/mcp
                          └── Feign 调用 law-law-service 数据管理接口

基础设施：Nacos / MySQL / Redis / Milvus / 阿里云 OSS
```

### 用户咨询链路

1. 前端提交问题，经网关进入 `law-ai-service`，校验身份与配额并组装会话上下文。
2. Java 调用 Python AI 服务，执行问题分析、缓存判断、记忆加载及知识检索。
3. Python 完成 Agent 推理和回答生成，返回流式文本与参考资料卡片。
4. Java 记录咨询结果与 Token 用量，并通过事务事件异步同步历史向量数据。

### 管理助手链路

1. 管理请求经网关进入 Java 管理助手接口，用户身份与角色传入 Python。
2. Router 进行意图分类、权限检查和子 Agent 分发。
3. 数据管理 Agent 调用按角色筛选的 MCP 工具；服务端继续校验身份与操作权限，通过 Feign 访问法律业务服务。
4. 需要补充参数或确认危险操作时暂停工作流，等待用户回复后恢复执行。

> `/mcp` 是服务间工具入口，不是前端公开接口。部署时应限制在可信内网访问，并将 Python 的 `MCP_LAW_AI_URL` 配置为 Java AI 服务地址。

## 技术栈

| 层次 | 技术与版本 | 用途 |
| --- | --- | --- |
| 前端 | Vue 3.5、Vite 4.5、Vue Router、Pinia | 页面、路由与状态管理。 |
| UI 与展示 | Element Plus、ECharts、Marked、Highlight.js | 管理界面、统计图表、Markdown 与代码高亮。 |
| Java 基础 | JDK 17、Spring Boot 3.5.13 | 微服务业务实现。 |
| 微服务 | Spring Cloud 2025.0.2、Spring Cloud Alibaba 2025.0.0.0 | Gateway、Nacos、OpenFeign。 |
| 数据访问 | MyBatis 3.0.5、PageHelper、Druid、MySQL | 持久化、分页与连接池。 |
| Java AI 集成 | Spring AI 1.1.2、Milvus Java SDK 2.6.20 | 模型集成、向量同步与 MCP Server。 |
| Python 基础 | Python 3.13+、FastAPI、Uvicorn、Pydantic | AI HTTP / SSE 服务与配置管理。 |
| Python AI | LangChain、LangGraph、OpenAI 兼容接口、DashScope | Agent 编排、模型调用与精排。 |
| MCP 客户端 | `langchain-mcp-adapters==0.3.2` | Java MCP 工具发现与调用。 |
| 向量与缓存 | Milvus、pymilvus 2.6+、Redis | 混合检索、语义缓存、会话与配置缓存。 |
| 安全与存储 | JWT（jjwt）、AOP RBAC、阿里云 OSS | 身份认证、角色授权与文件存储。 |

版本以根目录 `pom.xml`、`Web/vue-law/package.json` 和 `python-ai-service/pyproject.toml` 为准；Python 依赖的锁定版本见 `uv.lock`。

## 项目结构

```text
law-consultant-microservice/
├── Web/vue-law/           # Vue 用户端与管理端
├── law-gateway/           # 统一网关
├── law-user-service/      # 用户账号与游客服务
├── law-law-service/       # 法律内容、检索与收藏
├── law-ai-service/        # AI 业务桥接、配置、配额与 MCP Server
├── law-common-service/    # 公共业务服务
├── law-common/
│   ├── law-common-core/   # 实体、DTO、上下文、结果封装与事件
│   ├── law-common-security/ # JWT、拦截器与角色授权
│   ├── law-common-redis/  # Redis 工具封装
│   └── law-common-oss/    # OSS 集成
├── python-ai-service/     # RAG、记忆、缓存与管理 Agent
├── deploy/               # Dockerfile、Compose、Nginx 与 Milvus 初始化
└── docs/                 # 设计、迁移、部署资料与页面截图
```

## 快速开始

### 1. 环境要求

- JDK 17+、Maven 3.9+。
- Python 3.13+，建议使用 `uv` 管理依赖和虚拟环境。
- Node.js：建议 22+，并确认所用版本满足前端依赖要求。
- MySQL 8.0+、Redis 6+、Nacos 2.x。
- Milvus：建议使用 2.6 系列，并确认支持 BM25 Function、稀疏向量与中文分析器。
- 可用的模型服务凭证；上传与邮箱验证分别需要 OSS、SMTP 配置。

### 2. 准备数据库与配置中心

1. 启动 MySQL、Redis、Nacos 和 Milvus。
2. 准备独立开发数据库 `law_consultation`。仓库中的 `docs/law_consultation_backup.sql` 可作为结构参考，但包含数据与配置，必须检查后再导入，**不要直接导入已有生产数据库**。
3. 参考 [Nacos 配置资料](docs/nacos配置/) 在对应命名空间的 `DEFAULT_GROUP` 中准备配置，并核对各服务 `application.yml` 的 `spring.config.import`。

当前代码引用的 DataID 包括：

```text
common.yml
common-security.yml
common-oss.yml
law-gateway.yml
law-user-service.yml
law-law-service.yml
law-ai-service.yml
law-common-service.yml
```

> 配置导出与部分历史部署文档可能早于当前代码。请核对缺少的 DataID、数据库地址、服务地址及凭证，不要直接沿用示例中的值。

### 3. 配置 Python AI 服务

在 `python-ai-service/.env` 中填写项目配置。下面仅示意必要的基础配置，其他开关与参数见 [config.py](python-ai-service/app/core/config.py)：

```dotenv
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENAI_MODEL=your_qwen_model
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_MODEL=your_deepseek_model
DEEPSEEK_API_BASE_URL=https://api.deepseek.com

MILVUS_HOST=localhost
MILVUS_PORT=19530
MILVUS_DATABASE_NAME=law_ai
MILVUS_COLLECTION_ARTICLES=law_articles
MILVUS_COLLECTION_CASES=law_cases
MILVUS_COLLECTION_HISTORY=consult_history
MILVUS_METRIC_TYPE=COSINE

REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=2

JAVA_API_BASE_URL=http://localhost:8082
AI_CONFIG_URL=http://localhost:8083
MCP_LAW_AI_URL=http://localhost:8083/mcp
```

Java 侧在 Nacos 中配置 `python-ai-url: http://localhost:8000`。各端的 JWT、Redis 会话、数据库与 Milvus 配置需要保持一致。

### 4. 初始化 Milvus 知识库

集合结构参考 [Milvus 集合约束](docs/milvus集合约束/)，初始化脚本位于 [create_collections.py](deploy/milvus-init/create_collections.py)。在项目根目录执行：

```bash
uv sync --project python-ai-service
uv run --project python-ai-service python deploy/milvus-init/create_collections.py --host localhost --port 19530 --db law_ai
```

该脚本用于初始化 `law_articles`、`law_cases`、`consult_history` 和 `semantic_cache`。默认向量维度为 **1024**，需要与 Embedding 配置匹配。初始化后，通过管理端「同步知识库」导入法条与案例向量数据，否则 AI 无法检索到对应内容。

### 5. 构建与启动服务

先在项目根目录安装公共模块并构建 Java 服务：

```bash
mvn clean install -DskipTests
```

> 上述构建示例跳过测试，不代表测试已通过。验证项目时请另行运行相关测试。

随后在独立终端分别启动服务：

| 服务 | 默认端口 | 启动命令（项目根目录） |
| --- | --- | --- |
| `law-gateway` | 80 | `mvn -f law-gateway/pom.xml spring-boot:run` |
| `law-user-service` | 8081 | `mvn -f law-user-service/pom.xml spring-boot:run` |
| `law-law-service` | 8082 | `mvn -f law-law-service/pom.xml spring-boot:run` |
| `law-ai-service` | 8083 | `mvn -f law-ai-service/pom.xml spring-boot:run` |
| `law-common-service` | 8084 | `mvn -f law-common-service/pom.xml spring-boot:run` |
| `python-ai-service` | 8000 | 见下方 Python 命令。 |
| `Web/vue-law` | 5173 | 见下方前端命令。 |

Python AI 服务：

```bash
cd python-ai-service
uv sync
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

前端：

```bash
cd Web/vue-law
npm install
npm run dev
```

基础设施启动后，先启动 Java 业务服务，再启动 Python AI 服务与前端；确认相关服务在 Nacos 注册成功。网关可与 Java 业务服务一并启动，访问开发页面的默认地址为 `http://localhost:5173`。

前端开发环境通过 Vite 将 `/api` 请求转发到 `http://localhost:80` 并去掉前缀。若网关端口被占用或调整，需要同时修改网关配置及 [Vite 代理配置](Web/vue-law/vite.config.js)。

## Docker 部署

仓库提供基础设施与业务服务的 Docker Compose 编排、各服务 Dockerfile、Nginx 反向代理配置以及 Milvus 初始化脚本：

- [基础设施编排](deploy/infra.yml)：MySQL、Redis、Nacos、Milvus 及其依赖。
- [业务服务编排](deploy/docker-compose.yml)：前端、网关、Java 业务服务与 Python AI 服务。
- [详细部署方案](docs/Docker部署方案.md)：部署步骤、配置分工与排查说明。

部署前需要填写编排环境变量、Python `.env` 和 Nacos 配置，核对 SQL 挂载路径与 Milvus 版本，完成数据库和向量集合初始化。部分历史示例仍需按当前代码调整，不能将模板存在等同于可以无配置直接启动。

容器内的服务地址应使用服务名，而非 `localhost`，例如：

```dotenv
JAVA_API_BASE_URL=http://law-law-service:8082
AI_CONFIG_URL=http://law-ai-service:8083
MCP_LAW_AI_URL=http://law-ai-service:8083/mcp
```

外部流量经 Nginx 进入网关；业务端口、数据库、Redis、Milvus 与 MCP 端点应限制在可信网络内。生产环境应关闭开发调试配置并配置 HTTPS。

## 相关文档

| 文档 | 内容 |
| --- | --- |
| [架构图和技术栈](docs/架构图和技术栈.md) | 项目架构与技术选型资料。 |
| [AI Agent 平台架构](docs/ai-agent-platform-architecture.md) | AI 服务与 Agent 平台架构设计。 |
| [管理 Agent 设计](docs/admin-agent-design.md) | 管理助手与任务工作流设计。 |
| [MCP 服务实施设计](docs/MCP服务实施设计文档.md) | MCP v1 的接入方案与职责边界。 |
| [MCP 链路迁移手册 · Java 侧](docs/MCP链路迁移手册-Java侧.md) | Java MCP 工具与授权链路迁移说明。 |
| [LangGraph 工具工厂迁移手册 · Python 侧](docs/LangGraph工具工厂迁移手册-Python侧.md) | Python 工具绑定与调用迁移说明。 |
| [MCP 二期迭代规划](docs/MCP二期迭代规划.md) | 尚待推进的 MCP 后续演进，不作为已实现功能清单。 |
| [管理员权限分离与角色区分](docs/管理员权限分离与角色区分设计.md) | 管理员与超级管理员的权限设计。 |
| [游客用户体系实施计划](docs/游客用户体系实施计划.md) | 游客咨询、注册与数据迁移方案。 |
| [Docker 部署方案](docs/Docker部署方案.md) | 环境准备、容器部署与配置说明。 |

设计、规划和历史迁移资料用于解释方案背景，具体落地范围以当前代码为准。

## 安全与使用说明

- **密钥不得公开**：`.env`、Nacos 导出、数据库备份及部署模板可能包含凭证或业务数据；提交或分享前需要逐项检查、替换与脱敏。已泄露的凭证应撤销并轮换。
- **权限以后端为准**：前端菜单隐藏、Agent 路由和工具预筛选不能替代服务端授权；不要将业务服务或 `/mcp` 无限制暴露到公网。
- **知识库需要维护**：AI 检索依赖已入库资料，法条更新、失效或案例变更后需要及时同步，并核验引用来源。
- **模型与调用成本**：咨询效果依赖所用模型和资料质量，使用第三方模型服务会产生相应费用；Token 配额与使用统计用于辅助治理，不替代供应商账单。
