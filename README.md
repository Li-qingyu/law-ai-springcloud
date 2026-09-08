# 法律AI智能服务平台 (Law-AI-SpringCloud)

本项目是一个基于 **Spring Cloud 微服务 + RAG 检索增强生成 + 多 Agent 协作**的法律人工智能服务平台。用户可通过文字或流式（SSE）对话获得带信源引用的法律咨询；管理端基于 LangGraph 多 Agent 平台，支持用自然语言完成文件、数据、日志、权限等后台操作；并提供面向超级管理员的多 Provider AI 配置平台与 Token 配额治理能力。

## 系统架构

系统采用前后端分离设计。后端由 5 个 Spring Cloud 微服务、1 个 Python AI 服务及若干中间件组成：

```
Vue3 前端 (Web/vue-law)
        │
        ▼
law-gateway（唯一入口：路由 + JWT 三级鉴权 + 白名单）
        │
        ├──► law-user-service （用户 / 游客 / 邮箱验证）
        ├──► law-law-service  （法律条文 / 案例 / 书籍 / 类型 CRUD + 搜索）
        ├──► law-ai-service   （AI 咨询桥接 + Milvus 向量同步 + Token 配额 + AI 配置管理）
        └──► law-common-service（轮播图 / 文件上传 / 工作台统计）

law-ai-service ──(HTTP)──► python-ai-service（AI 核心：RAG 检索 / 三级记忆 / LangGraph 多 Agent）
python-ai-service ──(HTTP)──► law-law-service（管理端 Agent 调用后台 admin 接口）

基础设施：Nacos（注册&配置中心）｜ MySQL ｜ Redis ｜ Milvus ｜ 阿里云 OSS
```

数据流向：用户咨询请求经网关进入 `law-ai-service`，组装 Redis 会话历史后调用 Python AI 服务；Python 完成预分析、RAG 检索（Milvus）、Agent 推理与流式生成；结果回传 Java 侧落库（MySQL）、异步同步向量库（Milvus）、统计 Token 用量，并返回带信源引用的 `data_cards`。

## 核心功能

### 用户端
*   **智能法律咨询**：文字 / SSE 流式对话，答案附带法律条文、案例等信源引用（数据卡片）。
*   **跨会话记忆**：长期记忆基于 `consult_history` 向量集合按用户语义召回历史咨询，追问不失忆。
*   **会话管理**：查看历史咨询记录，管理咨询会话，清理历史。
*   **案例检索与收藏**：关键词搜索法律法规及司法案例，收藏感兴趣案例。
*   **游客体系**：免登录即可咨询，注册后游客数据自动迁移合并，无缝续聊。

### 管理端
*   **数据管理**：法律法规、案例、类型的增删改查，支持 Excel 批量导入以及 docx / pdf 脚本化导入。
*   **AI 多 Agent 助手**：LangGraph 工作流，路由（Router）+ 4 类子 Agent（文件/数据/日志/权限管理），自然语言驱动后台操作；高危操作通过 interrupt/resume 对话式确认。
*   **AI 配置平台**：多 Provider / 多模型运行时可热配置，按 provider 动态创建 LLM 实例。
*   **Token 配额治理**：按日/月双维度限流，全量埋点 Token 使用明细，定时自动重置。
*   **工作台统计**：展示用户、案例、法规等数据的增长趋势。
*   **三级权限控制**：super_admin / admin / user 权限矩阵 + 网关管理接口角色拦截（双层防护）。

## 项目亮点

*   **RAG 检索优化**：可插拔"策略 + 管道"检索架构（向量 / 混合 / 多路改写 3 种策略，去重 + 精排管道）；Dense 向量 + BM25 稀疏混合检索经 Milvus 服务端 RRF 融合，DashScope `gte-rerank` 精排并支持失败降级，召回率提升 30%+。
*   **AI 性能优化**：两阶段分离架构（轻量预分析 + Agent 推理 + 流式生成）使 Agent 推理循环 token 消耗降低 40%+；语义缓存高频问题命中 < 1s；意图路由（规则 + LLM 兜底）与并行工具调用进一步压缩延迟。
*   **分层记忆系统**：工作记忆 + 短期记忆（滚动摘要压缩）+ 长期记忆（Milvus 跨会话语义检索），并对手机号 / 身份证号等敏感信息做输入与存储双重脱敏。
*   **LangGraph 多 Agent 平台**：Router 路由 + 权限校验 + 子 Agent 分发的两段式工作流设计；利用 `interrupt`/`resume` 实现删除、导入等高危操作的对话式确认；三级权限矩阵控制各 Agent 操作集。
*   **AI 配置平台 + Token 配额**：ConfigManager 三级降级链（Redis → Java 内部接口 → env）支持运行时可热改模型配置；Token 按日/月限流、异步埋点、定时重置。
*   **工程化实践**：事件驱动向量同步（`@TransactionalEventListener(AFTER_COMMIT)` + 异步），数据库与 Milvus 解耦；游客数据事务化迁移合并；网关多级 JWT 鉴权并向下游透传身份。

## 技术栈

### 后端 (Java)
*   **框架**: Spring Boot 3 / Spring Cloud 2025.0.2（Nacos、Gateway）/ Spring AI 1.1.2
*   **数据库**: MySQL 8（MyBatis-Plus + Druid 连接池），Redis
*   **AI 集成**: Spring AI（OpenAI ChatModel / EmbeddingModel / VectorStore，用于 Java 侧向量同步与内部模型调用）
*   **向量库**: Milvus + `milvus-sdk-java`
*   **安全**: JWT（jjwt），网关全局过滤器鉴权
*   **文档**: knife4j

### AI 服务 (Python 3.13+)
*   **框架**: FastAPI + uvicorn
*   **LLM 集成**: LangChain（OpenAI Tools Agent），DashScope / DeepSeek 等多 Provider 通过 OpenAI 兼容接口接入
*   **Agent 框架**: LangGraph（状态图 + checkpointer，支持 interrupt/resume 断点续跑）
*   **向量检索**: pymilvus（Dense + BM25 稀疏混合检索、RRF 融合、语义缓存）
*   **记忆**: 工作记忆 / 短期记忆（滚动摘要）/ 长期记忆（跨会话语义检索）+ 隐私脱敏

### 中间件
*   Nacos（服务发现 + 配置中心）｜ MySQL 8+ ｜ Redis 6+ ｜ Milvus 2.x（pymilvus 2.6+）｜ 阿里云 OSS

## 项目模块概览

| 模块名称 | 描述 |
| :--- | :--- |
| **law-gateway** | 网关服务，统一路由 + JWT 三级鉴权（游客/用户/管理员），白名单与角色拦截。 |
| **law-user-service** | 用户账号服务：注册登录、邮箱验证、游客体系（游客咨询 + 注册后数据迁移）。 |
| **law-law-service** | 法律核心业务服务：Article / Book / Case / Type 的 CRUD、导入导出与搜索。 |
| **law-ai-service** | AI 业务入口：咨询桥接（Java↔Python）、会话管理、Milvus 向量同步、Token 配额、AI 配置管理。 |
| **law-common-service** | 公共业务服务：轮播图、文件上传、工作台统计。 |
| **python-ai-service** | Python AI 核心：RAG 检索、三级记忆、LangGraph 多 Agent、SSE 流式、语义缓存。 |
| **law-common-core** | 通用核心包：实体类（Entity）、DTO、统一结果封装（Result）、事件定义、数据卡片。 |
| **law-common-security** | 安全组件：JWT 工具、拦截器、用户上下文（BaseContext）。 |
| **law-common-redis** | Redis 封装工具类。 |
| **law-common-oss** | 阿里云 OSS 文件上传集成。 |

## 快速开始

### 环境要求
*   JDK 17+
*   Python 3.13+
*   MySQL 8.0+、Redis 6+、Milvus 2.x、Nacos 2.x（作为配置中心与注册中心）

### 基础设施准备
1.  启动 MySQL、Redis、Milvus、Nacos（`startup.cmd -m standalone`）。
2.  创建 Milvus 集合：`law_articles` / `law_cases` / `consult_history` / `semantic_cache`（集合约束参考 `docs/milvus集合约束/`，`semantic_cache` 由 Python 服务启动时自动创建）。
3.  导入各服务配置到 Nacos（参考 `docs/nacos配置/`）。

### 启动服务

| 服务 | 端口 | 启动方式 |
|------|------|----------|
| law-gateway | 80 | `mvn spring-boot:run` |
| law-user-service | 8081 | `mvn spring-boot:run` |
| law-law-service | 8082 | `mvn spring-boot:run` |
| law-ai-service | 8083 | `mvn spring-boot:run` |
| law-common-service | 8084 | `mvn spring-boot:run` |
| python-ai-service | 8000 | 见下 |
| Web/vue-law | 5173 | `cd Web/vue-law && npm install && npm run dev` |

Python AI 服务（使用 uv，项目为 `pyproject.toml` 管理依赖）：

```bash
cd python-ai-service
uv sync                 # 或 pip install -e .
uvicorn app.main:app --reload --port 8000
```

> 约定启动顺序：基础设施 → `law-gateway` → 业务服务 → `python-ai-service`。Java 侧通过 `python-ai-url` 配置指向 Python 服务（Docker 部署时指向服务名 `python-ai-service`）。

### 配置说明

*   **Nacos**：Java 服务所有环境配置（数据源、Redis、OSS、JWT、Milvus、`python-ai-url` 等）均由 Nacos 下发。
*   **Python 服务**：`python-ai-service/app/core/config.py` 读取 `.env` / 环境变量（Milvus、Redis、DashScope Key、`JAVA_API_BASE_URL` 等）。
*   **Aliyun OSS**：上传功能需配置 Endpoint、AccessKey、BucketName。
*   **JWT**：在 `law-common-security` / Nacos 中配置 SecretKey 与 Token 过期时间。

## 部署

支持 Docker 一键部署，见 `deploy/`（各服务 Dockerfile + `docker-compose.yml`）与文档 `docs/Docker部署方案.md`；Nacos 配置导出备份位于 `deploy/nacos_config_export_*.zip`。

## 关键实现特性

*   **SSE 流式响应**：AI 咨询支持流式输出，实时返回生成内容。
*   **事件驱动向量同步**：`@TransactionalEventListener(AFTER_COMMIT)` + `@Async` 实现数据库事务与 Milvus 向量同步的解耦与最终一致。
*   **语义缓存**：Milvus 向量语义缓存，高频问题直接命中，命中响应 < 1s。
*   **LangGraph 多 Agent**：管理端自然语言驱动后台 API，高危操作对话式确认。
*   **三级记忆 + 隐私脱敏**：工作 / 短期 / 长期记忆分层，敏感信息双重脱敏。
*   **多 Provider 热切换**：AI 配置平台运行时可改模型配置，三级降级链保证可用性。
*   **Token 配额治理**：按日/月限流 + 全量 Token 使用埋点。