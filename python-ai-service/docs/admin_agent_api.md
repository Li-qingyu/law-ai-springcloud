# 管理员Agent API文档

## 概述

管理员Agent系统提供RESTful API接口，支持文件管理、日志管理、数据管理和权限管理功能。

## API端点

### 统一管理接口

#### POST /admin/manage
统一管理接口，根据查询内容自动路由到相应的子Agent。

**请求体：**
```json
{
  "query": "上传文件 patent_data.xlsx",
  "user_id": 123,
  "user_role": "super_admin",
  "task_params": {}
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "文件上传成功"
  }
}
```

### 文件管理

#### POST /admin/file/upload
文件上传接口

**请求体：**
```json
{
  "query": "上传文件 patent_data.xlsx",
  "user_id": 123,
  "user_role": "super_admin"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "文件上传成功"
  }
}
```

### 日志管理

#### POST /admin/logs/query
日志查询接口

**请求体：**
```json
{
  "query": "查询系统日志",
  "user_id": 123,
  "user_role": "super_admin"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "系统日志查询完成"
  }
}
```

### 数据管理

#### POST /admin/data/manage
数据管理接口

**请求体：**
```json
{
  "query": "管理专利数据",
  "user_id": 123,
  "user_role": "super_admin"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "专利数据管理完成"
  }
}
```

### 权限管理

#### POST /admin/permission/manage
权限管理接口

**请求体：**
```json
{
  "query": "管理用户",
  "user_id": 123,
  "user_role": "super_admin"
}
```

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "result": "用户管理完成"
  }
}
```

## 错误处理

所有API在发生错误时返回以下格式：

```json
{
  "code": 500,
  "message": "error message",
  "data": null
}
```

## 权限说明

- **super_admin**：拥有所有权限
- **data_admin**：文件管理和数据管理权限
- **log_admin**：日志管理权限
- **user_admin**：权限管理权限

## 使用示例

### Python 示例

```python
import requests

# 文件上传
response = requests.post("http://localhost:8000/admin/file/upload", json={
    "query": "上传文件 patent_data.xlsx",
    "user_id": 123,
    "user_role": "super_admin"
})
print(response.json())

# 日志查询
response = requests.post("http://localhost:8000/admin/logs/query", json={
    "query": "查询系统日志",
    "user_id": 123,
    "user_role": "super_admin"
})
print(response.json())

# 数据管理
response = requests.post("http://localhost:8000/admin/data/manage", json={
    "query": "管理专利数据",
    "user_id": 123,
    "user_role": "super_admin"
})
print(response.json())

# 权限管理
response = requests.post("http://localhost:8000/admin/permission/manage", json={
    "query": "管理用户",
    "user_id": 123,
    "user_role": "super_admin"
})
print(response.json())
```

### cURL 示例

```bash
# 文件上传
curl -X POST "http://localhost:8000/admin/file/upload" \
  -H "Content-Type: application/json" \
  -d '{"query": "上传文件 patent_data.xlsx", "user_id": 123, "user_role": "super_admin"}'

# 日志查询
curl -X POST "http://localhost:8000/admin/logs/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "查询系统日志", "user_id": 123, "user_role": "super_admin"}'

# 数据管理
curl -X POST "http://localhost:8000/admin/data/manage" \
  -H "Content-Type: application/json" \
  -d '{"query": "管理专利数据", "user_id": 123, "user_role": "super_admin"}'

# 权限管理
curl -X POST "http://localhost:8000/admin/permission/manage" \
  -H "Content-Type: application/json" \
  -d '{"query": "管理用户", "user_id": 123, "user_role": "super_admin"}'
```
