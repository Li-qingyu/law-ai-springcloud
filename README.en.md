# Legal AI Intelligent Service Platform (Law-AI-SpringCloud)

This project is a legal artificial intelligence service platform based on the Spring Cloud microservice architecture. It integrates Large Language Models (LLM), Vector Search (RAG), and Agent technology, aiming to provide users with intelligent legal consultation, regulation and case retrieval, and backend management functions.

## System Architecture

The system adopts a frontend-backend separation design. The backend consists of multiple Spring Cloud microservices and Python AI services:

*   **API Gateway (`law-gateway`)**: Unified traffic entry point, responsible for routing forwarding and authentication.
*   **AI Service (`law-ai-service`)**: Processes user AI consultation requests, interfaces with the Python backend AI service, manages session history, and syncs data to the vector database.
*   **Legal Service (`law-law-service`)**: Responsible for CRUD, import/export, and search of core data such as legal provisions, books, cases, and types.
*   **User Service (`law-user-service`)**: Handles user registration, login, information management, email verification, etc.
*   **Common Service (`law-common-service`)**: Provides general business capabilities such as carousel management, file upload, and dashboard statistics.
*   **Python AI Service (`python-ai-service`)**: Core Brain, developed based on Python, includes RAG retrieval augmentation generation, multi-Agent collaboration (Admin mode), long-short term memory management, etc.

## Core Functions

### User Side
*   **Intelligent Legal Consultation**: Users can obtain legal advice through text or streaming (SSE) conversation.
*   **Case Retrieval**: Search relevant laws, regulations, and judicial cases based on keywords.
*   **Session Management**: View historical consultation records and manage consultation sessions.
*   **Case Bookmarking**: Bookmark cases of interest for future viewing.

### Admin Side
*   **Data Management**: Add, delete, modify, and query laws, regulations, cases, and types; supports Excel import.
*   **AI Admin Agent**: Administrators can perform file management, data operations, log queries, and permission management via the AI assistant.
*   **Dashboard Statistics**: Display growth trends for data such as users, cases, and regulations.

## Tech Stack

### Backend (Java)
*   **Frameworks**: Spring Boot, Spring Cloud (Nacos, Gateway)
*   **Databases**: MySQL, Redis (Cache)
*   **ORM**: MyBatis-Plus
*   **AI Integration**: Spring AI (Integration with OpenAI/LLM)
*   **Vector Database**: Milvus (For semantic retrieval of legal provisions and cases)
*   **Security**: JWT (jjwt)

### AI Service (Python)
*   **Framework**: FastAPI
*   **LLM Integration**: Compatible with OpenAI API
*   **Vector Search**: Milvus Client
*   **Agent Framework**: LangChain / Proprietary Workflow (Supports Agents such as Admin Router, Data Management, File Management, etc.)
*   **Retrieval Augmentation**: Rerank, Reciprocal Rank Fusion (RRF)

## Project Module Overview

| Module Name | Description |
| :--- | :--- |
| **law-gateway** | Gateway service, uniformly handles request routing and JWT authentication. |
| **law-ai-service** | AI business entry point, processes consultation requests, bridges Java and Python services, manages session state. |
| **law-law-service** | Legal core business service, manages Article, Book, Case, Type, provides search APIs. |
| **law-user-service** | User account service, handles login, registration, and permission-related logic. |
| **law-common-service** | Public business service, provides carousel, upload, general query, and other functions. |
| **python-ai-service** | AI core service written in Python, includes RAG retrieval, Agent logic, and memory management. |
| **law-common-core** | General core package, contains Entity classes, Data Transfer Objects (DTO), Result encapsulation (Result), etc. |
| **law-common-security** | Security-related components, such as JWT tools, interceptors, and user context (BaseContext). |
| **law-common-redis** | Redis encapsulation utility classes. |
| **law-common-oss** | Alibaba Cloud OSS file upload integration. |

## Quick Start

### Environment Requirements
*   JDK 17+
*   Python 3.10+
*   MySQL 8.0+
*   Redis 6+
*   Milvus 2.3+
*   Nacos (As configuration center and service discovery)

### Startup Sequence

1.  **Configure Nacos**: Import `application.yml` configurations for each module into Nacos.
2.  **Start Infrastructure**: Ensure MySQL, Redis, and Milvus are running normally.
3.  **Start Microservices**:
    *   Start `law-gateway`
    *   Start `law-ai-service`
    *   Start `law-law-service`
    *   Start `law-user-service`
    *   Start `law-common-service`
4.  **Start AI Service**:
    *   Enter the `python-ai-service` directory, install dependencies (`pip install -r requirements.txt` or use `uv`).
    *   Run `uvicorn app.main:app --reload`.

### Configuration Instructions

*   **Aliyun OSS**: Configure Endpoint, AccessKey, BucketName in `law-common-oss` or Nacos.
*   **Milvus**: Configure connection information in `law-ai-service` and `python-ai-service`.
*   **JWT**: Configure SecretKey and Token expiration time in `law-common-security`.

## Key Implementation Features

*   **SSE Streaming Response**: AI consultation supports streaming output, returning generated content in real-time.
*   **Event-Driven Synchronization**: Uses Spring `@TransactionalEventListener` to decouple database operations and Milvus vector synchronization.
*   **Multi-Level Cache**: Combines Redis and Semantic Cache (in Python) to optimize AI response speed.
*   **Agent Admin Mode**: Administrators can call backend APIs via natural language, e.g., "Query new cases added in the past week".