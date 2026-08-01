

# 法律AI智能服务平台 (Law-AI-SpringCloud)

本项目是一个基于 Spring Cloud 微服务架构的法律人工智能服务平台，集成了大语言模型（LLM）、向量检索（RAG）以及智能体（Agent）技术，旨在为用户提供智能法律咨询、法规案例检索以及后台管理等功能。

## 系统架构

系统采用前后端分离设计，后端由多个 Spring Cloud 微服务和 Python AI 服务组成：

*   **API 网关 (`law-gateway`)**: 统一流量入口，负责路由转发、鉴权。
*   **AI 服务 (`law-ai-service`)**: 处理用户 AI 咨询请求，对接 Python 后端 AI 服务，管理会话历史，同步数据到向量数据库。
*   **法律服务 (`law-law-service`)**: 负责法律条文、书籍、案例、类型等核心数据的 CRUD、导入导出及搜索。
*   **用户服务 (`law-user-service`)**: 处理用户注册、登录、信息管理、邮箱验证等。
*   **公共服务 (`law-common-service`)**: 提供轮播图管理、文件上传、工作台统计等通用业务能力。
*   **Python AI 服务 (`python-ai-service`)**: 核心大脑，基于 Python 开发，包含 RAG 检索增强生成、多 Agent 协作（管理员模式）、长短期记忆管理等。

## 核心功能

### 用户端
*   **智能法律咨询**: 用户可通过文字或流式（SSE）对话获取法律建议。
*   **案例检索**: 根据关键词搜索相关法律法规及司法案例。
*   **会话管理**: 查看历史咨询记录，管理咨询会话。
*   **案例收藏**: 收藏感兴趣的案例以便后续查看。

### 管理端
*   **数据管理**: 法律法规、案例、类型的增删改查，支持 Excel 导入。
*   **AI 管理员 Agent**: 管理员可通过 AI 助手进行文件管理、数据操作、日志查询及权限管理等。
*   **工作台统计**: 展示用户、案例、法规等数据的增长趋势。

## 技术栈

### 后端 (Java)
*   **框架**: Spring Boot, Spring Cloud (Nacos, Gateway)
*   **数据库**: MySQL, Redis (缓存)
*   **ORM**: MyBatis-Plus
*   **AI 集成**: Spring AI (对接 OpenAI/LLM)
*   **向量库**: Milvus (用于法律条文和案例的语义检索)
*   **安全**: JWT (jjwt)

### AI 服务 (Python)
*   **框架**: FastAPI
*   **LLM 集成**: 兼容 OpenAI API
*   **向量检索**: Milvus Client
*   **Agent 框架**: LangChain / 自研工作流 (支持 Admin Router, Data Management, File Management 等 Agent)
*   **检索增强**: Rerank, Reciprocal Rank Fusion (RRF)

## 项目模块概览

| 模块名称 | 描述 |
| :--- | :--- |
| **law-gateway** | 网关服务，统一处理请求路由和 JWT 鉴权。 |
| **law-ai-service** | AI 业务入口，处理咨询请求，桥接 Java 与 Python 服务，管理会话状态。 |
| **law-law-service** | 法律核心业务服务，管理 Article, Book, Case, Type，提供搜索 API。 |
| **law-user-service** | 用户账号服务，处理登录、注册、权限相关逻辑。 |
| **law-common-service** | 公共业务服务，提供轮播图、上传、通用查询等功能。 |
| **python-ai-service** | Python 编写的 AI 核心服务，包含 RAG 检索、Agent 逻辑、内存管理。 |
| **law-common-core** | 通用核心包，包含实体类 (Entity)、数据传输对象 (DTO)、结果封装 (Result) 等。 |
| **law-common-security** | 安全相关组件，如 JWT 工具、拦截器、用户上下文 (BaseContext)。 |
| **law-common-redis** | Redis 封装工具类。 |
| **law-common-oss** | 阿里云 OSS 文件上传集成。 |

## 快速开始

### 环境要求
*   JDK 17+
*   Python 3.10+
*   MySQL 8.0+
*   Redis 6+
*   Milvus 2.3+
*   Nacos (作为配置中心与服务发现)

### 启动顺序

1.  **配置 Nacos**: 导入各模块 `application.yml` 配置到 Nacos。
2.  **启动基础设施**: 确保 MySQL, Redis, Milvus 正常运行。
3.  **启动微服务**:
    *   启动 `law-gateway`
    *   启动 `law-ai-service`
    *   启动 `law-law-service`
    *   启动 `law-user-service`
    *   启动 `law-common-service`
4.  **启动 AI 服务**:
    *   进入 `python-ai-service` 目录，安装依赖 (`pip install -r requirements.txt` 或使用 `uv`)。
    *   运行 `uvicorn app.main:app --reload`。

### 配置说明

*   **Aliyun OSS**: 在 `law-common-oss` 或 Nacos 中配置 Endpoint, AccessKey, BucketName。
*   **Milvus**: 在 `law-ai-service` 和 `python-ai-service` 中配置连接信息。
*   **JWT**: 在 `law-common-security` 中配置 SecretKey 和 Token 过期时间。

## 关键实现特性

*   **SSE 流式响应**: AI 咨询支持流式输出，实时返回生成内容。
*   **事件驱动同步**: 使用 Spring `@TransactionalEventListener` 实现数据库操作与 Milvus 向量同步的解耦。
*   **多级缓存**: 结合 Redis 和语义缓存 (Semantic Cache in Python) 优化 AI 响应速度。
*   **Agent 管理员模式**: 管理员可通过自然语言调用后端 API，如“查询过去一周新增的案例”。