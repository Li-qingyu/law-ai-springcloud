# Legal AI Intelligent Service Platform (Law-AI-SpringCloud)

This project is a legal AI service platform built on **Spring Cloud microservices + RAG (Retrieval-Augmented Generation) + multi-agent collaboration**. Users can get legal consultation with source citations via text or streaming (SSE) conversation. On the admin side, a LangGraph multi-agent platform supports natural-language-driven backend operations over files, data, logs and permissions. It also provides a multi-provider AI configuration platform and Token quota governance for super admins.

## System Architecture

The system adopts a frontend/backend separation design. The backend consists of 5 Spring Cloud microservices, 1 Python AI service, plus supporting middleware:

```
Vue3 Frontend (Web/vue-law)
        │
        ▼
law-gateway (single entry: routing + JWT 3-tier auth + whitelist)
        │
        ├──► law-user-service  (users / guests / email verification)
        ├──► law-law-service   (laws / cases / books / types CRUD + search)
        ├──► law-ai-service    (AI consultation bridge + Milvus vector sync + Token quota + AI config management)
        └──► law-common-service (carousel / file upload / dashboard statistics)

law-ai-service ──(HTTP)──► python-ai-service (AI core: RAG retrieval / 3-tier memory / LangGraph multi-agent)
python-ai-service ──(HTTP)──► law-law-service (admin agents call backend admin APIs)

Infrastructure: Nacos (registry & config center) ｜ MySQL ｜ Redis ｜ Milvus ｜ Aliyun OSS
```

Data flow: a user consultation request enters `law-ai-service` through the gateway, which assembles the Redis session history and calls the Python AI service. Python performs pre-analysis, RAG retrieval (Milvus), agent reasoning and streaming generation. Results are returned to the Java side for persistence (MySQL), async vector-database synchronization (Milvus), and Token usage accounting, together with source-cited `data_cards`.

## Core Features

### User Side
*   **Intelligent Legal Consultation**: text / SSE streaming conversation; answers come with source citations (data cards) of laws and cases.
*   **Cross-session Memory**: long-term memory performs user-scoped semantic retrieval over the `consult_history` vector collection, so follow-ups do not lose context.
*   **Session Management**: view historical consultations and manage / clear sessions.
*   **Case Retrieval & Bookmarking**: keyword search over laws and judicial cases; bookmark cases of interest.
*   **Guest System**: consult without login; guest data is auto-migrated and merged after registration for seamless continuation.

### Admin Side
*   **Data Management**: CRUD for laws, cases and types; supports Excel bulk import and docx / pdf scripted import.
*   **AI Multi-Agent Assistant**: a LangGraph workflow with a Router plus 4 sub-agents (file / data / log / permission management) that drives backend operations via natural language; high-risk operations are confirmed conversationally via interrupt/resume.
*   **AI Config Platform**: hot-configurable multi-provider / multi-model settings; LLM instances are created per provider at runtime.
*   **Token Quota Governance**: daily / monthly dual-dimension rate limiting, full Token usage instrumentation, and scheduled auto-reset.
*   **Dashboard Statistics**: growth trends for users, cases, laws, etc.
*   **3-tier Access Control**: super_admin / admin / user permission matrix + role interception on gateway admin paths (defense in depth).

## Project Highlights

*   **RAG Retrieval Optimization**: pluggable "strategy + pipeline" architecture (vector / hybrid / multi-query strategies with dedup + rerank pipelines); hybrid Dense + BM25 retrieval fused server-side via Milvus RRF, DashScope `gte-rerank` refinement with graceful fallback — recall improved by 30%+.
*   **AI Performance Optimization**: two-stage architecture (lightweight pre-analysis + agent reasoning + streaming generation) cuts agent-reasoning token usage by 40%+; semantic cache answers frequent queries in < 1s; intent routing (rule + LLM fallback) and parallel tool calls further reduce latency.
*   **Layered Memory System**: working memory + short-term memory (rolling summary compression) + long-term memory (Milvus cross-session semantic retrieval), with dual desensitization of sensitive data (phone numbers, ID numbers, etc.) at both LLM input and storage.
*   **LangGraph Multi-Agent Platform**: two-stage workflow design (Router routing + permission check + sub-agent dispatch); conversational confirmation of high-risk operations (delete / import) via `interrupt`/`resume`; a 3-tier permission matrix governs each agent's operations.
*   **AI Config Platform + Token Quota**: a 3-level degradation chain in ConfigManager (Redis → Java internal API → env) enables hot model-config changes at runtime; Token rate limiting per day/month, async instrumentation and scheduled reset.
*   **Engineering Practices**: event-driven vector sync (`@TransactionalEventListener(AFTER_COMMIT)` + async) decouples the database from Milvus; transactional guest-data migration & merge; gateway multi-level JWT auth with identity propagated downstream.

## Tech Stack

### Backend (Java)
*   **Frameworks**: Spring Boot 3 / Spring Cloud 2025.0.2 (Nacos, Gateway) / Spring AI 1.1.2
*   **Databases**: MySQL 8 (MyBatis-Plus + Druid pool), Redis
*   **AI Integration**: Spring AI (OpenAI ChatModel / EmbeddingModel / VectorStore — used for Java-side vector sync and internal model calls)
*   **Vector Database**: Milvus + `milvus-sdk-java`
*   **Security**: JWT (jjwt), gateway global-filter auth
*   **Docs**: knife4j

### AI Service (Python 3.13+)
*   **Framework**: FastAPI + uvicorn
*   **LLM Integration**: LangChain (OpenAI Tools Agent); DashScope / DeepSeek and other providers via OpenAI-compatible APIs
*   **Agent Framework**: LangGraph (state graph + checkpointer, supports interrupt/resume)
*   **Vector Search**: pymilvus (Dense + BM25 sparse hybrid search, RRF fusion, semantic cache)
*   **Memory**: working / short-term (rolling summary) / long-term (cross-session semantic retrieval) + privacy desensitization

### Middleware
*   Nacos (service discovery + config center) ｜ MySQL 8+ ｜ Redis 6+ ｜ Milvus 2.x (pymilvus 2.6+) ｜ Aliyun OSS

## Project Module Overview

| Module | Description |
| :--- | :--- |
| **law-gateway** | Gateway: unified routing + 3-tier JWT auth (guest / user / admin), whitelist and role interception. |
| **law-user-service** | User account service: registration / login, email verification, guest system (guest consultation + post-registration data migration). |
| **law-law-service** | Legal core service: CRUD, import/export and search for Article / Book / Case / Type. |
| **law-ai-service** | AI business entry: consultation bridge (Java↔Python), session management, Milvus vector sync, Token quota, AI config management. |
| **law-common-service** | Common business service: carousel, file upload, dashboard statistics. |
| **python-ai-service** | Python AI core: RAG retrieval, 3-tier memory, LangGraph multi-agent, SSE streaming, semantic cache. |
| **law-common-core** | Common core package: entities, DTOs, unified Result wrapper, events, data cards. |
| **law-common-security** | Security components: JWT utilities, interceptors, user context (BaseContext). |
| **law-common-redis** | Redis wrapper utilities. |
| **law-common-oss** | Aliyun OSS file-upload integration. |

## Quick Start

### Environment Requirements
*   JDK 17+
*   Python 3.13+
*   MySQL 8.0+, Redis 6+, Milvus 2.x, Nacos 2.x (config center & service discovery)

### Infrastructure Preparation
1.  Start MySQL, Redis, Milvus and Nacos (`startup.cmd -m standalone`).
2.  Create the Milvus collections `law_articles` / `law_cases` / `consult_history` / `semantic_cache` (see `docs/milvus集合约束/`; `semantic_cache` is auto-created by the Python service on startup).
3.  Import per-service configuration into Nacos (see `docs/nacos配置/`).

### Start the Services

| Service | Port | Start |
|------|------|----------|
| law-gateway | 80 | `mvn spring-boot:run` |
| law-user-service | 8081 | `mvn spring-boot:run` |
| law-law-service | 8082 | `mvn spring-boot:run` |
| law-ai-service | 8083 | `mvn spring-boot:run` |
| law-common-service | 8084 | `mvn spring-boot:run` |
| python-ai-service | 8000 | see below |
| Web/vue-law | 5173 | `cd Web/vue-law && npm install && npm run dev` |

Python AI service (dependency management via `pyproject.toml`, use uv):

```bash
cd python-ai-service
uv sync                 # or pip install -e .
uvicorn app.main:app --reload --port 8000
```

> Recommended start order: infrastructure → `law-gateway` → business services → `python-ai-service`. The Java side points to the Python service via the `python-ai-url` config (service name `python-ai-service` in Docker deployments).

### Configuration Notes

*   **Nacos**: all Java service environment config (datasource, Redis, OSS, JWT, Milvus, `python-ai-url`, etc.) is delivered from Nacos.
*   **Python service**: `python-ai-service/app/core/config.py` reads `.env` / environment variables (Milvus, Redis, DashScope key, `JAVA_API_BASE_URL`, etc.).
*   **Aliyun OSS**: upload requires Endpoint, AccessKey and BucketName.
*   **JWT**: configure SecretKey and token expiration in `law-common-security` / Nacos.

## Deployment

Docker one-click deployment is supported — see `deploy/` (per-service Dockerfiles + `docker-compose.yml`) and `docs/Docker部署方案.md`; Nacos config export backup is at `deploy/nacos_config_export_*.zip`.

## Key Implementation Features

*   **SSE Streaming Response**: AI consultations stream output back in real time.
*   **Event-Driven Vector Sync**: `@TransactionalEventListener(AFTER_COMMIT)` + `@Async` decouple database transactions from Milvus synchronization with eventual consistency.
*   **Semantic Cache**: Milvus vector semantic cache answers frequent questions directly, in < 1s on hit.
*   **LangGraph Multi-Agent**: admin-side natural language drives backend APIs, with conversational confirmation of high-risk operations.
*   **3-tier Memory + Privacy Desensitization**: working / short-term / long-term memory layers; sensitive data is doubly desensitized.
*   **Multi-Provider Hot Switch**: the AI config platform changes model settings at runtime via a 3-level degradation chain.
*   **Token Quota Governance**: daily/monthly rate limiting + full Token usage instrumentation.