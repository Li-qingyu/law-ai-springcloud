# Python AI服务实现方案

## 项目背景

当前法律咨询项目已有基于Spring AI的Agent工具调用方案（详见`logical-sleeping-dongarra.md`），但希望在不改动现有前端代码和Spring Boot主体业务逻辑的前提下，构建一个基于Python的、能力完全等同于原Spring AI方案的AI能力服务。

### 核心需求
1. **功能对等**: 提供与Spring AI方案完全相同的AI能力，包括：
   - Agent工具调用模式
   - 法律条文、案例、咨询历史的向量检索
   - 数据卡片生成和跳转支持
   - 会话管理
2. **无缝集成**: 不改变现有前端调用方式和Spring Boot主体业务逻辑
3. **性能要求**: 端到端响应时间 < 3秒

## 技术栈选型

### 已确定选型
| 组件 | 技术选择 | 理由 |
|------|----------|------|
| Web框架 | **FastAPI** | 现代、高性能、自动API文档生成 |
| AI框架 | **LangChain** | 成熟的Agent和工具调用支持，社区活跃 |
| 向量数据库客户端 | **PyMilvus** | 官方Python SDK，功能完整 |
| LLM调用 | **OpenAI SDK** | 兼容阿里云通义千问的OpenAI兼容接口 |
| 嵌入模型 | **阿里云text-embedding-v3** | 与现有方案保持一致 |

### 备选评估
| 方案 | 优点 | 缺点 | 决策 |
|------|------|------|------|
| FastAPI + LangChain | 开发效率高，功能全面 | 依赖较多，学习曲线 | ✅ **采用** |
| FastAPI + 自定义Agent | 更灵活轻量 | 开发量较大，需要自研工具调用 | 未采用 |
| Flask + LangChain | 轻量级 | 性能不如FastAPI，异步支持较弱 | 未采用 |

## 整体架构设计

### 架构概览
```
┌─────────────────┐    HTTP Request    ┌────────────────────┐
│                 │ ─────────────────> │                    │
│  前端(Vue项目)  │                    │  Spring Boot应用   │
│                 │ <───────────────── │   (Java, 主业务)   │
└─────────────────┘    HTTP Response   └─────────┬──────────┘
                                                 │ HTTP REST API
                                                 │ (AI咨询转发)
                                                 ▼
┌─────────────────────────────────────────────────────────┐
│                                                         │
│              Python AI服务 (FastAPI + LangChain)        │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Agent服务  │  │  工具管理器  │  │  上下文处理   │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬────────┘  │
│         │                │                  │           │
│  ┌──────▼──────┐  ┌─────▼──────┐   ┌──────▼────────┐  │
│  │ LangChain   │  │ 自定义工具 │   │  Redis缓存    │  │
│  │  Agent执行  │  │  - 条文搜索 │   │  (结果缓存)   │  │
│  └──────┬──────┘  │  - 案例搜索 │   └───────────────┘  │
│         │         │  - 历史搜索 │                      │
│         │         └─────┬───────┘                      │
│  ┌──────▼───────────────▼───────┐                      │
│  │       LLM调用层              │                      │
│  │   (阿里云通义千问)           │                      │
│  └──────────────┬───────────────┘                      │
│                 │                                      │
│  ┌──────────────▼───────────────┐                      │
│  │      向量检索层              │                      │
│  │   (PyMilvus客户端)           │                      │
│  │   - 仅查询Milvus元数据       │                      │
│  │   - 不直接访问MySQL          │                      │
│  └──────────────┬───────────────┘                      │
│  ┌──────────────▼────────────────────────────────────┐ │
│  │                基础设施层                         │ │
│  │         Milvus向量数据库 (Docker)                │ │
│  │             MySQL数据库                          │ │
│  │             Redis缓存                            │ │
│  └──────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 组件职责

#### 1. Spring Boot应用（现有）- **会话管理中心**
- **会话管理**: 维护用户对话历史（最近5轮），存储到Redis
- **用户认证**: 验证用户身份和权限
- **上下文组装**: 为用户当前问题组装完整的对话上下文
- **请求转发**: 调用Python AI服务进行AI推理
- **咨询记录**: 同步保存咨询记录到MySQL（状态：处理中→完成）
- **响应返回**: 统一格式响应返回给前端

#### 2. Python AI服务（新建）- **无状态AI推理**
- **API网关层**: FastAPI应用，提供RESTful接口
- **Agent服务层**: LangChain驱动的Agent，协调工具调用
- **工具层**: 自定义工具实现（条文搜索、案例搜索、历史搜索）
- **向量检索层**: PyMilvus客户端，执行相似度搜索（**仅通过Milvus元数据获取信息**）
- **LLM层**: OpenAI SDK调用阿里云通义千问，基于完整上下文生成答案
- **数据卡片生成**: 从Milvus元数据生成前端数据卡片
- **重要原则**: Python服务无状态，每次请求接收完整上下文，不维护会话状态

#### 3. 数据存储（现有）
- **MySQL**: 存储用户信息、法律条文、案例、咨询记录等结构化数据
- **Milvus**: 存储向量化后的法律条文、案例、咨询历史（含完整元数据）
- **Redis**: 存储用户会话历史（7天TTL），键格式：`session:{session_id}:{user_id}`

## Python AI服务详细设计

### 1. API接口设计
```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

# 对话消息格式（与OpenAI兼容）
class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]  # 消息角色
    content: str  # 消息内容
    timestamp: Optional[datetime] = None  # 时间戳（可选）

# 请求格式（Java → Python）
class AiConsultRequest(BaseModel):
    question: str  # 用户当前问题
    session_id: str  # 会话ID（前端传递，Java验证）
    user_id: Optional[int] = None  # 用户ID（Java传递）
    conversation_history: List[ConversationMessage]  # 最近5轮对话历史（Java组装）
    # 格式示例：
    # [
    #   {"role": "user", "content": "劳动合同解除需要赔偿吗？"},
    #   {"role": "assistant", "content": "根据《劳动合同法》第46条..."},
    #   {"role": "user", "content": "那具体赔偿标准是什么？"}
    # ]

# 响应格式（Python → Java）
class AiConsultResponse(BaseModel):
    answer: str  # AI生成的答案（Markdown格式）
    data_cards: List[DataCard]  # 相关数据卡片
    session_id: str  # 会话ID（原样返回）
    turn_number: int  # 当前轮次（Java计算）

class DataCard(BaseModel):
    type: Literal["law_article", "law_case", "consult_history"]
    id: int  # 数据源ID（来自Milvus元数据source_id）
    title: str  # 卡片标题（来自Milvus元数据title）
    summary: str  # 摘要信息（来自Milvus元数据summary）
    relevance: float  # 相关度评分（0-1，Milvus搜索分数）
    detail_url: Optional[str] = None  # 详情页URL（前端根据type和id生成）
```

**API端点**:
- `POST /v1/ai/consult` - **AI法律咨询（核心接口）**，接收完整上下文，返回AI答案和数据卡片
- `GET /v1/ai/health` - 服务健康检查（调试用）
- `GET /v1/ai/sessions/{session_id}` - **调试接口**，查看Python处理的上下文（仅开发环境）

### 1.1 数据访问原则（关键设计）
Python AI服务**仅通过Milvus向量数据库获取所需信息**，不直接访问MySQL。数据访问遵循以下原则：

1. **元数据存储**: 所有必要信息存储在Milvus文档的元数据字段中
   ```python
   # Milvus文档结构示例
   document = {
       "id": "unique_doc_id",
       "content": "法律条文或案例的详细内容...",
       "metadata": {
           "source_id": 123,           # 对应MySQL表中的ID
           "type": "law_article",      # 数据类型
           "title": "中华人民共和国劳动合同法第四十六条",
           "summary": "用人单位解除劳动合同的经济补偿规定",
           "content_json": "{\"full_content\":\"...\"}"  # 完整的JSON内容
       }
   }
   ```

2. **信息完整性**: Milvus中存储的元数据包含：
   - `source_id`: 对应MySQL表的主键ID
   - `type`: 数据类型（law_article/law_case/consult_history）
   - `title`: 标题，用于数据卡片显示
   - `summary`: 摘要，用于数据卡片显示
   - `content_json`: 完整的JSON序列化内容，包含LLM生成答案所需的所有信息

3. **数据同步保障**: 由Spring Boot应用负责MySQL到Milvus的数据同步
   - 数据变更时自动同步到Milvus
   - 定时一致性检查确保数据完整
   - Python服务无需关心数据同步逻辑

### 2. Agent工具设计

#### 工具基类
```python
class BaseSearchTool(BaseTool):
    """搜索工具基类"""
    def __init__(self, collection_name: str, milvus_client):
        self.collection_name = collection_name
        self.milvus_client = milvus_client

    def _search(self, query: str, top_k: int = 10, score_threshold: float = 0.6):
        """执行向量相似度搜索（仅从Milvus元数据获取信息）"""
        # 1. 查询向量化
        embedding = embedding_model.embed_query(query)

        # 2. Milvus搜索（同时检索向量和元数据）
        results = milvus_client.search(
            collection_name=self.collection_name,
            data=[embedding],
            limit=top_k,
            param={"metric_type": "COSINE", "params": {"nprobe": 10}},
            output_fields=["source_id", "type", "title", "summary", "content_json"]  # 指定需要返回的元数据字段
        )

        # 3. 结果过滤（基于相关度阈值）和格式化
        filtered_results = [
            result for result in results
            if result.get("score", 0) >= score_threshold
        ]

        # 4. 从元数据中提取信息，不访问MySQL
        return self._format_from_metadata(filtered_results)
```

#### 具体工具实现（均从Milvus元数据获取信息）
1. **LawArticleSearchTool**: 法律条文搜索
   - 功能: 根据问题语义搜索相关法律条文
   - 数据源: 从Milvus `law_articles`集合的元数据中获取
   - 输入: query (string)
   - 输出: JSON列表，包含条文ID（source_id）、标题、内容摘要（来自content_json）

2. **LawCaseSearchTool**: 案例搜索
   - 功能: 搜索相关法律案例
   - 数据源: 从Milvus `law_cases`集合的元数据中获取
   - 输入: query (string)
   - 输出: JSON列表，包含案例ID（source_id）、标题、摘要

3. **ConsultHistorySearchTool**: 咨询历史搜索
   - 功能: 搜索相似历史咨询问题
   - 数据源: 从Milvus `consult_history`集合的元数据中获取
   - 输入: query (string)
   - 输出: JSON列表，包含咨询ID（source_id）、问题、答案摘要

### 3. LangChain Agent配置
```python
def create_agent(tools: List[BaseTool], llm: BaseChatModel):
    """创建带工具调用的Agent"""

    # 系统提示词（与Spring AI保持一致）
    system_prompt = """你是一个专业的法律咨询助手，能够根据用户问题搜索相关法律条文、案例和历史咨询记录。
    请根据以下步骤处理用户问题：
    1. 分析问题类型，决定需要调用哪些搜索工具
    2. 调用相应的搜索工具获取相关信息
    3. 基于搜索结果，生成专业、准确的法律咨询答案
    4. 在答案中引用相关法律依据，并说明出处

    回答格式要求：
    - 使用Markdown格式
    - 重要法律条文使用**加粗**强调
    - 案例引用使用>引用块格式
    """

    # 创建Agent
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=PromptTemplate.from_template(system_prompt)
    )

    return agent
```

### 4. 数据卡片生成器
```python
class DataCardBuilder:
    """将工具返回结果转换为前端数据卡片"""

    @staticmethod
    def from_milvus_results(results: List[Dict], data_type: str) -> List[DataCard]:
        """从Milvus搜索结果生成数据卡片（仅使用元数据）"""
        cards = []
        for result in results:
            # 从Milvus元数据中提取信息，不访问MySQL
            metadata = result.get("metadata", {})
            card = DataCard(
                type=data_type,
                id=metadata.get("source_id", 0),  # 来自元数据的source_id
                title=metadata.get("title", ""),
                summary=metadata.get("summary", ""),
                relevance=result.get("score", 0.0),
                # detail_url由前端根据type和id生成
                # 例如：type=law_article, id=123 → /user/law/detail/123
            )
            cards.append(card)
        return cards
```

## 数据传输格式

基于Java中心化会话管理架构，各组件间的数据传输遵循以下格式：

### 1. 前端 → Java 数据格式

**API端点**: `POST /api/home/ai-consult`

**请求格式**:
```json
{
  "question": "劳动合同解除需要赔偿吗？",
  "session_id": "uuid-generated-by-frontend"
}
```

**字段说明**:
- `question`: 用户提出的法律咨询问题（必填）
- `session_id`: 会话标识符（必填）
  - 首次咨询：前端生成UUID
  - 连续对话：使用现有session_id
  - 新会话：生成新UUID

**请求头**:
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

### 2. Java → Python 数据格式

**API端点**: `POST {python-service}/v1/ai/consult`

**请求格式** (对应Python的`AiConsultRequest`):
```json
{
  "question": "劳动合同解除需要赔偿吗？",
  "session_id": "uuid-generated-by-frontend",
  "user_id": 123,
  "conversation_history": [
    {
      "role": "user",
      "content": "历史问题1",
      "timestamp": "2026-04-16T10:30:00Z"
    },
    {
      "role": "assistant",
      "content": "历史答案1",
      "timestamp": "2026-04-16T10:30:05Z"
    },
    {
      "role": "user",
      "content": "历史问题2",
      "timestamp": "2026-04-16T10:32:00Z"
    }
  ]
}
```

**字段说明**:
- `question`: 用户当前问题（Java从前端接收）
- `session_id`: 会话标识符（Java原样传递）
- `user_id`: 用户ID（Java从JWT解析）
- `conversation_history`: 对话历史（Java从Redis获取并组装）
  - **格式**: 最近5轮对话（最多10条消息，user和assistant各一条为一轮）
  - **角色**: `"user"` 或 `"assistant"`
  - **内容**: 消息文本
  - **时间戳**: ISO 8601格式（可选）

### 3. Python → Java 数据格式

**响应格式** (对应Python的`AiConsultResponse`):
```json
{
  "answer": "根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同...",
  "data_cards": [
    {
      "type": "law_article",
      "id": 456,
      "book_id": 123,
      "article_title": "中华人民共和国劳动合同法第四十六条",
      "content": "用人单位解除劳动合同的经济补偿规定",
      "relevance": 0.92,
      "detail_url": null
    },
    {
      "type": "law_case",
      "id": 789,
      "title": "张某与某公司劳动争议案",
      "type_id": 1 ,
      "tags": "劳动争议 合同",
      "content": "关于违法解除劳动合同赔偿金的典型案例",
      "judgment": "某公司向张某起诉，要求enzyme公司赔偿enzyme公司因不按约而放弃的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE",
      "cover": "https://example.com/judgment.pdf",
      "relevance": 0.85,
      "detail_url": null
    },
    {
      "type": "law_consult_history",
      "id": 123,
      "user_id": 123,
      "session_id": "uuid-generated-by-frontend",
      "question": "劳动合同解除需要赔偿吗？",
      "answer": "根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同...",
      "relevance": 0.75,
      "detail_url": null
    }
  ],
  "session_id": "uuid-generated-by-frontend",
  "turn_number": 3
}
```

**字段说明**:
- `answer`: AI生成的答案（Markdown格式，包含法律依据和解释）
- `data_cards`: 相关数据卡片列表
  - `type`: 数据类型（`"law_article"`, `"law_case"`, `"consult_history"`）
  - `id`: 数据源ID（对应MySQL表中的主键）
  - `title`: 卡片标题
  - `summary`: 摘要信息
  - `relevance`: 相关度评分（0-1，来自Milvus搜索分数）
  - `detail_url`: 详情页URL（前端生成，Python返回null）
- `session_id`: 会话标识符（原样返回）
- `turn_number`: 当前轮次（Python计算或Java传递）

### 4. Java → 前端 数据格式

**响应格式**:
```json
{
  "code": 200,
  "message": "成功",
  "data": {
    "answer": "根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同...",
    "data_cards": [
      {
          "type": "law_article",
          "id": 456,
          "book_id": 123,
          "article_title": "中华人民共和国劳动合同法第四十六条",
          "content": "用人单位解除劳动合同的经济补偿规定",
          "relevance": 0.92,
          "detail_url": null
      },
      {
          "type": "law_case",
          "id": 789,
          "title": "张某与某公司劳动争议案",
          "type_id": 1 ,
          "tags": "劳动争议 合同",
          "content": "关于违法解除劳动合同赔偿金的典型案例",
          "judgment": "某公司向张某起诉，要求enzyme公司赔偿enzyme公司因不按约而放弃的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE 1.1节所规定的enzyme公司所CLAUSE",
          "cover": "https://example.com/judgment.pdf",
          "relevance": 0.85,
          "detail_url": null
      },
      {
          "type": "law_consult_history",
          "id": 123,
          "user_id": 123,
          "session_id": "uuid-generated-by-frontend",
          "question": "劳动合同解除需要赔偿吗？",
          "answer": "根据《劳动合同法》第46条规定，用人单位在以下情形解除劳动合同...",
          "relevance": 0.75,
          "detail_url": null
      }
    ],
    "session_id": "uuid-generated-by-frontend",
    "turn_number": 3,
    "consultation_id": 12345,
    "created_at": "2026-04-16T10:35:00Z"
  },
  "timestamp": "2026-04-16T10:35:02Z"
}
```

**字段说明**:
- **外层标准响应**:
  - `code`: 状态码（200=成功，其他=错误）
  - `message`: 状态描述
  - `data`: 业务数据
  - `timestamp`: 响应时间戳
- **内层业务数据** (`data`字段):
  - `answer`: AI答案（来自Python）
  - `data_cards`: 数据卡片（Python返回，Java补充`detail_url`）
  - `session_id`: 会话标识符
  - `turn_number`: 当前轮次
  - `consultation_id`: 咨询记录ID（Java生成）
  - `created_at`: 咨询创建时间

**`detail_url`生成规则**:
```javascript
// 前端或Java根据type和id生成详情页URL
function generateDetailUrl(type, id) {
  switch (type) {
    case "law_article":
      return `/user/law/detail/${id}`;
    case "law_case":
      return `/user/case/detail/${id}`;
    case "consult_history":
      return `/user/ai/history/${id}`;
    default:
      return "#";
  }
}
```

## 集成方案

### 1. Spring Boot集成点
在现有的AI咨询服务层添加Python服务调用：

```java
@Service
public class AiConsultationServiceImpl implements AiConsultationService {

    @Autowired
    private PythonAiServiceClient pythonAiClient;

    @Override
    public AiConsultResponse consult(AiConsultRequest request) {
        // 1. 参数验证和预处理
        // 2. 调用Python AI服务
        PythonAiResponse pythonResponse = pythonAiClient.consult(request);

        // 3. 转换为Spring Boot响应格式
        AiConsultResponse response = convertToResponse(pythonResponse);

        // 4. 保存咨询记录到MySQL
        saveConsultationRecord(request, response);

        return response;
    }
}
```

### 2. Python服务客户端（Java端）
```java
@Component
public class PythonAiServiceClient {

    @Value("${python.ai.service.url:http://localhost:8000}")
    private String pythonServiceUrl;

    public PythonAiResponse consult(AiConsultRequest request) {
        // 使用RestTemplate或WebClient调用Python服务
        // POST {pythonServiceUrl}/v1/ai/consult
    }
}
```

### 3. 配置项
```yaml
# application.yml 新增配置
python:
  ai:
    service:
      url: http://localhost:8000  # Python服务地址
      timeout: 5000               # 超时时间(ms)
      retry:
        max-attempts: 3           # 最大重试次数
        backoff-delay: 1000       # 重试间隔(ms)
```

## 数据流设计

### 1. 用户问答流程（Java中心化会话管理）
```
1. 用户在前端提交问题
   → POST /api/home/ai-consult
   → 携带：question、session_id（前端生成/传递）

2. Spring Boot接收请求并管理会话
   → 用户认证和参数验证
   → 从Redis获取session历史（最近5轮）
   → 创建咨询记录到MySQL（状态：处理中）
   → 组装完整上下文：问题 + 会话历史（格式：ConversationMessage列表）

3. Spring Boot调用Python AI服务（无状态推理）
   → POST {python-service}/v1/ai/consult
   → 携带：question、session_id、user_id、conversation_history（完整上下文）

4. Python AI服务处理（无状态）
   → LangChain Agent基于完整上下文分析问题
   → 决定调用哪些搜索工具
   → 工具执行：查询Milvus向量数据库（仅从元数据获取信息）
   → LLM基于「上下文 + Milvus检索结果」生成答案
   → DataCardBuilder从元数据生成数据卡片
   → 返回：answer、data_cards、session_id（原样返回）

5. Spring Boot更新会话和记录
   → 更新Redis会话：添加用户问题 + AI答案（保留最近5轮）
   → 更新MySQL咨询记录：填充答案、数据卡片、状态→完成
   → 返回统一响应给前端

6. 前端展示结果
   → 显示AI答案（Markdown渲染）
   → 展示数据卡片（可点击跳转）
   → 更新会话UI显示历史对话
```

### 2. 知识库同步流程（保持现有）
- **数据变更自动同步**: Spring Boot服务在数据变更时自动更新Milvus
- **定时一致性检查**: 每日凌晨2点检查MySQL和Milvus数据一致性
- **Python服务只读**: Python AI服务仅查询Milvus，不写入（包括consult_history集合）
- **咨询记录保存**: 咨询记录由Spring Boot保存到MySQL，然后同步到Milvus

## 部署方案

### 部署原则
基于用户确认的要求：
1. **同一服务器部署**: Spring Boot应用和Python AI服务部署在同一台物理服务器/虚拟机
2. **容器化编排**: 使用Docker Compose进行容器编排和管理
3. **网络隔离**: 通过Docker网络实现服务间通信，避免端口冲突
4. **资源隔离**: 每个服务在独立容器中运行，资源限制和监控

### 1. 开发环境
```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   Spring Boot   │ HTTP  │   Python AI     │       │   Milvus        │
│   (localhost:8080)│──────>│   (localhost:8000)│<──────│   (Docker)     │
└─────────────────┘       └─────────────────┘       └─────────────────┘
        │                         │                         │
        ▼                         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   MySQL         │       │   Redis         │       │   前端Vue项目   │
│   (localhost:3306)│       │   (localhost:6379)│       │   (开发服务器)  │
└─────────────────┘       └─────────────────┘       └─────────────────┘
```

### 2. 生产环境（推荐） - 同一服务器容器化编排

**架构特点**：
- **单机多容器**: 所有服务运行在同一服务器的Docker容器中
- **内部网络**: 使用Docker内部网络进行服务通信，提高安全性
- **资源限制**: 为每个容器设置CPU和内存限制，避免资源竞争
- **服务发现**: 通过Docker服务名进行内部服务发现

**网络设计**：
```
┌─────────────────────────────────────────────────────────────────────┐
│                       同一物理服务器/虚拟机                           │
│                                                                     │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐      │
│  │  Spring Boot  │    │  Python AI    │    │    Milvus     │      │
│  │  容器(8080)   │    │  容器(8000)   │    │   容器(19530) │      │
│  └───────┬───────┘    └───────┬───────┘    └───────┬───────┘      │
│          │                    │                    │              │
│  ┌───────▼───────┐    ┌───────▼───────┐    ┌───────▼───────┐      │
│  │   MySQL容器   │    │   Redis容器   │    │   前端代理    │      │
│  │    (3306)     │    │    (6379)     │    │   (Nginx)     │      │
│  └───────────────┘    └───────────────┘    └───────────────┘      │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │                    Docker内部网络                           │    │
│  │              (所有容器通过服务名互相访问)                     │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
```

```yaml
# Docker Compose编排（同一服务器）
version: '3.8'
services:
  # 现有服务
  mysql:
    image: mysql:8.0
    # ... 现有配置

  redis:
    image: redis:7-alpine
    # ... 现有配置

  milvus:
    image: milvusdb/milvus:v2.3.0
    # ... 现有配置

  spring-boot-app:
    build: ./law-ai-service
    depends_on:
      - mysql
      - redis
      - milvus
    environment:
      PYTHON_AI_SERVICE_URL: http://python-ai-service:8000
    # 资源限制（同一服务器上避免资源竞争）
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 1G
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/actuator/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
    # ... 现有配置

  # 新增服务
  python-ai-service:
    build: ./python-ai-service
    ports:
      - "8000:8000"
    depends_on:
      - milvus
      - redis
    environment:
      MILVUS_HOST: milvus
      MILVUS_PORT: 19530
      REDIS_HOST: redis
      REDIS_PORT: 6379
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      OPENAI_BASE_URL: https://dashscope.aliyuncs.com/compatible-mode
    # 资源限制（同一服务器上避免资源竞争）
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    # 健康检查
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 2.1 同一服务器部署要点

#### 资源规划建议
| 服务 | CPU限制 | 内存限制 | 说明 |
|------|---------|----------|------|
| Spring Boot应用 | 4核心 | 4GB | 主业务逻辑，需要较多资源 |
| Python AI服务 | 2核心 | 2GB | AI推理，CPU密集型 |
| MySQL | 2核心 | 2GB | 数据库，内存敏感 |
| Milvus | 4核心 | 4GB | 向量检索，CPU和内存密集 |
| Redis | 1核心 | 1GB | 缓存（会话存储+结果缓存） |
| **总计** | **13核心** | **13GB** | 推荐服务器配置：16核心/32GB内存 |

#### 部署脚本示例
```bash
#!/bin/bash
# deploy.sh - 同一服务器部署脚本

# 1. 环境变量配置
export OPENAI_API_KEY="your-api-key"
export DB_PASSWORD="your-db-password"
export REDIS_PASSWORD="your-redis-password"

# 2. 创建Docker网络（如果不存在）
docker network create law-ai-network || true

# 3. 启动所有服务
docker-compose -f docker-compose.yml up -d

# 4. 等待服务启动
echo "等待服务启动..."
sleep 30

# 5. 检查服务状态
docker-compose ps
docker-compose logs --tail=20 spring-boot-app
docker-compose logs --tail=20 python-ai-service

# 6. 健康检查
curl -f http://localhost:8080/actuator/health || echo "Spring Boot服务异常"
curl -f http://localhost:8000/health || echo "Python AI服务异常"
```

#### 运维命令参考
```bash
# 查看所有容器状态
docker-compose ps

# 查看日志
docker-compose logs -f python-ai-service  # Python服务日志
docker-compose logs -f spring-boot-app    # Spring Boot日志

# 资源使用监控
docker stats

# 重启单个服务
docker-compose restart python-ai-service

# 更新服务（重新构建镜像）
docker-compose build python-ai-service
docker-compose up -d python-ai-service

# 备份数据
docker-compose exec mysql mysqldump -u root -p$DB_PASSWORD law_consultation > backup.sql
```

### 3. 监控和运维
- **健康检查**: Python服务提供`/health`端点
- **日志收集**: 结构化日志输出，集成ELK
- **性能监控**: Prometheus + Grafana监控响应时间、错误率
- **自动扩缩容**: 基于CPU/内存使用率自动调整Python服务实例数

## 实施步骤

### 阶段一：Python AI服务基础框架（1周）
1. **项目初始化**
   - 创建Python项目结构（FastAPI + LangChain）
   - 配置依赖管理（requirements.txt或poetry）
   - 设置开发环境配置

2. **基础设施集成**
   - 实现PyMilvus客户端连接（配置元数据字段访问）
   - 配置OpenAI SDK（阿里云兼容模式）
   - 设置Redis连接（可选，用于缓存或其他用途）
   - 验证Milvus元数据完整性（确保所有必要字段存在）

3. **基础API实现**
   - FastAPI应用骨架
   - 健康检查端点
   - 基础请求/响应模型

### 阶段二：Agent工具调用实现（2周）
4. **工具定义和实现（元数据访问）**
   - 实现BaseSearchTool基类，支持从Milvus元数据提取信息
   - 开发三个具体搜索工具，仅使用Milvus元数据字段
   - 工具测试（验证元数据访问的正确性）

5. **LangChain Agent集成**
   - 配置LangChain Agent
   - 实现工具调用逻辑
   - 系统提示词优化

6. **数据卡片生成**
   - 实现DataCardBuilder
   - 测试数据转换逻辑

### 阶段三：Spring Boot集成（1周）
7. **Java客户端开发**
   - 实现PythonAiServiceClient
   - 配置HTTP客户端（重试、超时）
   - 错误处理和降级策略

8. **Spring Boot服务集成（含会话管理）**
   - **会话管理实现**：Redis存储用户对话历史（最近5轮，7天TTL）
   - **上下文组装**：从Redis获取历史，组装ConversationMessage格式上下文
   - **咨询记录管理**：同步创建/更新咨询记录到MySQL（状态跟踪）
   - **AiConsultationService重构**：集成会话管理、上下文组装、Python服务调用
   - **前端兼容性**：保持原有API接口不变，session_id由前端传递
   - **集成测试**：完整流程测试（前端→Java→Python→Java→前端）

### 阶段四：测试和部署（1周）
9. **端到端测试**
   - 功能测试：完整问答流程
   - 性能测试：响应时间、并发能力
   - 集成测试：Spring Boot + Python服务

10. **部署和监控**
    - Docker镜像构建
    - 生产环境部署
    - 监控配置

## 风险和缓解措施

### 1. 技术风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LangChain学习曲线 | 开发进度延迟 | 提供详细示例和文档，前期重点学习核心功能 |
| Python-Java集成复杂度 | 集成失败 | 采用简单HTTP REST API，定义清晰的接口契约 |
| Milvus查询性能 | 响应时间超时 | 优化索引参数，设置查询超时，实现结果缓存 |
| LLM API稳定性 | 服务不可用 | 实现重试机制，设置备选LLM服务 |

### 2. 运维风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| Python服务部署复杂度 | 部署失败 | 提供完整Docker配置和部署脚本 |
| 多服务监控困难 | 问题排查慢 | 统一日志格式，集成集中式监控 |
| 数据一致性 | 搜索结果不准确 | 保持现有同步机制，Python服务只读 |
| Milvus元数据不完整 | 无法生成完整数据卡片 | 验证元数据字段，Spring Boot同步时确保字段完整性 |
| 容器资源竞争 | 同一服务器上服务性能下降 | 设置合理的资源限制，监控资源使用情况 |

### 3. 业务风险
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 答案质量下降 | 用户满意度降低 | 严格测试，与Spring AI方案结果对比 |
| 响应时间增加 | 用户体验差 | 性能优化，异步处理非关键任务 |

## 成功标准

1. **功能对等性**: Python服务提供与Spring AI方案完全相同的功能
2. **性能指标**: 端到端响应时间 < 3秒（P95）
3. **集成透明性**: 前端无需修改，Spring Boot主体业务逻辑不变
4. **可用性**: 服务可用性 > 99.5%
5. **开发效率**: 总实施时间控制在5周内

## 关键设计决策总结

基于用户确认的要求，本方案做出以下关键设计决策：

### 1. 数据访问策略
- **仅通过Milvus元数据**: Python服务不直接访问MySQL，所有信息从Milvus文档的元数据字段获取
- **元数据字段要求**: Milvus中必须包含完整的元数据字段：`source_id`, `type`, `title`, `summary`, `content_json`
- **数据同步责任**: Spring Boot负责MySQL到Milvus的数据同步，确保元数据完整性

### 2. 部署架构
- **同一服务器容器化**: Spring Boot和Python服务部署在同一服务器的Docker容器中
- **资源隔离**: 通过Docker资源限制避免服务间资源竞争
- **内部网络通信**: 使用Docker内部网络进行服务发现和通信

### 3. 集成方式
- **HTTP REST API**: Spring Boot通过HTTP调用Python服务，简单可靠
- **功能对等**: Python服务提供与Spring AI方案完全相同的API接口
- **无缝切换**: 前端无需修改，Spring Boot仅作请求转发

### 4. 会话管理策略（新增）
- **Java中心化会话管理**: Spring Boot负责维护用户对话历史（Redis存储，7天TTL）
- **Python无状态推理**: 每次请求接收完整上下文（最近5轮对话），不维护会话状态
- **上下文传递格式**: 标准化ConversationMessage格式，与OpenAI API兼容
- **同步数据持久化**: Java同步保存咨询记录到MySQL，确保数据一致性

## 下一步行动

1. **详细设计评审**: 评审本方案，确认技术细节
2. **环境准备**: 搭建Python开发环境，配置测试Milvus实例
3. **原型开发**: 实现最小可行原型，验证技术选型
4. **迭代开发**: 按照实施步骤分阶段开发

---

*本文档为初步方案，具体实现细节可根据实际情况调整。*