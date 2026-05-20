# 法律咨询系统微服务化改造完整操作手册

## 版本信息

- **文档版本**: v1.1
- **更新日期**: 2026-05-20
- **Nacos 版本**: 3.2.1
- **Spring Cloud Alibaba**: 2023.0.1.2
- **Java 版本**: 17+

## 背景

当前项目 `law-consultant-project` 是单体 Spring Boot 应用，需要进行微服务化改造。本方案采用**新建独立仓库**的方式，使用**共享数据库**策略，确保原仓库不受影响。

---

## 目录

1. [环境准备](#一环境准备)
2. [创建新仓库](#二创建新仓库)
3. [父 POM 配置](#三父-pom-配置)
4. [公共模块创建](#四公共模块创建)
5. [网关服务创建](#五网关服务创建)
6. [用户服务创建](#六用户服务创建)
7. [法典服务创建](#七法典服务创建)
8. [AI 服务改造](#八ai-服务改造)
9. [通用服务创建](#九通用服务创建)
10. [Nacos 配置](#十nacos-配置)
11. [Docker 部署配置](#十一docker-部署配置)
12. [测试验证](#十二测试验证)

---

## 一、环境准备

### 1.1 基础环境

| 软件 | 版本要求 | 说明 |
|------|----------|------|
| JDK | 17+ | 保持与原项目一致 |
| Maven | 3.8+ | 构建工具 |
| MySQL | 8.0+ | 数据库 |
| Redis | 7.x | 缓存 |
| Nacos | 3.2.1 | 注册中心 + 配置中心 |
| Milvus | 2.4.x | 向量数据库（AI 服务需要） |

### 1.2 安装 Nacos

```bash
# 下载 Nacos 3.2.1
wget https://github.com/alibaba/nacos/releases/download/3.2.1/nacos-server-3.2.1.tar.gz

# 解压
tar -xzf nacos-server-3.2.1.tar.gz

# 单机模式启动
cd nacos/bin
./startup.sh -m standalone

# Windows 系统使用
# startup.cmd -m standalone

# 访问控制台
# http://localhost:8848/nacos
# 默认账号密码: nacos/nacos
```

**注意**: Nacos 3.x 版本需要 Java 17+ 运行环境

### 1.3 创建 Nacos 数据库

```sql
CREATE DATABASE IF NOT EXISTS nacos DEFAULT CHARSET utf8mb4;
USE nacos;

-- 执行 Nacos 自带的 SQL 脚本
-- 位置: nacos/conf/mysql-schema.sql
```

---

## 二、创建新仓库

### 2.1 创建仓库

```bash
# 创建新仓库目录
mkdir law-consultant-microservice
cd law-consultant-microservice

# 初始化 Git
git init

# 创建 .gitignore
cat > .gitignore << 'EOF'
# IDE
.idea/
*.iml
.vscode/

# Maven
target/
*.jar
*.war

# Logs
*.log
logs/

# OS
.DS_Store
Thumbs.db

# Environment
.env
*.env.local
EOF

# 首次提交
git add .
git commit -m "初始化微服务项目结构"
```

### 2.2 创建目录结构

```bash
# 创建所有目录
mkdir -p law-common/law-common-core/src/main/java/org/law/common/core/{result,exception,constant,utils,entity}
mkdir -p law-common/law-common-redis/src/main/java/org/law/common/redis/{config,utils}
mkdir -p law-common/law-common-security/src/main/java/org/law/common/security/{utils,config,interceptor,annotation}
mkdir -p law-common/law-common-oss/src/main/java/org/law/common/oss/{config,utils}

mkdir -p law-gateway/src/main/java/org/law/gateway/filter
mkdir -p law-gateway/src/main/resources

mkdir -p law-user-service/src/main/java/org/law/user/{controller,service,mapper,entity,dto,vo}
mkdir -p law-user-service/src/main/resources/mapper

mkdir -p law-law-service/src/main/java/org/law/law/{controller/admin,controller/user,service,mapper,entity}
mkdir -p law-law-service/src/main/resources/mapper

mkdir -p law-ai-service/src/main/java/org/law/ai/{controller,service,feign,mapper,entity}
mkdir -p law-ai-service/src/main/resources/mapper

mkdir -p law-common-service/src/main/java/org/law/common/service/{controller,service,mapper,entity}
mkdir -p law-common-service/src/main/resources/mapper

mkdir -p sql
```

---

## 三、父 POM 配置

### 3.1 创建根目录 pom.xml

**文件**: `law-consultant-microservice/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>3.5.11</version>
        <relativePath/>
    </parent>

    <groupId>org.law</groupId>
    <artifactId>law-consultant-microservice</artifactId>
    <packaging>pom</packaging>
    <version>1.0.0-SNAPSHOT</version>
    <name>law-consultant-microservice</name>
    <description>法律咨询系统微服务版</description>

    <modules>
        <module>law-common</module>
        <module>law-gateway</module>
        <module>law-user-service</module>
        <module>law-law-service</module>
        <module>law-ai-service</module>
        <module>law-common-service</module>
    </modules>

    <properties>
        <java.version>17</java.version>
        <spring-cloud.version>2023.0.1</spring-cloud.version>
        <spring-cloud-alibaba.version>2023.0.1.2</spring-cloud-alibaba.version>
        <spring-ai.version>1.1.2</spring-ai.version>
        <mybatis.spring>3.0.5</mybatis.spring>
        <lombok>1.18.42</lombok>
        <fastjson>1.2.76</fastjson>
        <druid>1.2.1</druid>
        <pagehelper>2.1.1</pagehelper>
        <aliyun.sdk.oss>3.17.4</aliyun.sdk.oss>
        <knife4j>4.3.0</knife4j>
        <jjwt>0.9.1</jjwt>
        <milvus>2.4.5</milvus>
    </properties>

    <dependencyManagement>
        <dependencies>
            <!-- Spring Cloud -->
            <dependency>
                <groupId>org.springframework.cloud</groupId>
                <artifactId>spring-cloud-dependencies</artifactId>
                <version>${spring-cloud.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>

            <!-- Spring Cloud Alibaba -->
            <dependency>
                <groupId>com.alibaba.cloud</groupId>
                <artifactId>spring-cloud-alibaba-dependencies</artifactId>
                <version>${spring-cloud-alibaba.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>

            <!-- Spring AI -->
            <dependency>
                <groupId>org.springframework.ai</groupId>
                <artifactId>spring-ai-bom</artifactId>
                <version>${spring-ai.version}</version>
                <type>pom</type>
                <scope>import</scope>
            </dependency>

            <!-- MyBatis -->
            <dependency>
                <groupId>org.mybatis.spring.boot</groupId>
                <artifactId>mybatis-spring-boot-starter</artifactId>
                <version>${mybatis.spring}</version>
            </dependency>

            <!-- Lombok -->
            <dependency>
                <groupId>org.projectlombok</groupId>
                <artifactId>lombok</artifactId>
                <version>${lombok}</version>
            </dependency>

            <!-- Fastjson -->
            <dependency>
                <groupId>com.alibaba</groupId>
                <artifactId>fastjson</artifactId>
                <version>${fastjson}</version>
            </dependency>

            <!-- Druid -->
            <dependency>
                <groupId>com.alibaba</groupId>
                <artifactId>druid-spring-boot-starter</artifactId>
                <version>${druid}</version>
            </dependency>

            <!-- PageHelper -->
            <dependency>
                <groupId>com.github.pagehelper</groupId>
                <artifactId>pagehelper-spring-boot-starter</artifactId>
                <version>${pagehelper}</version>
            </dependency>

            <!-- Knife4j -->
            <dependency>
                <groupId>com.github.xiaoymin</groupId>
                <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
                <version>${knife4j}</version>
            </dependency>

            <!-- JWT -->
            <dependency>
                <groupId>io.jsonwebtoken</groupId>
                <artifactId>jjwt</artifactId>
                <version>${jjwt}</version>
            </dependency>

            <!-- Aliyun OSS -->
            <dependency>
                <groupId>com.aliyun.oss</groupId>
                <artifactId>aliyun-sdk-oss</artifactId>
                <version>${aliyun.sdk.oss}</version>
            </dependency>

            <!-- Milvus -->
            <dependency>
                <groupId>io.milvus</groupId>
                <artifactId>milvus-sdk-java</artifactId>
                <version>${milvus}</version>
            </dependency>
        </dependencies>
    </dependencyManagement>

    <repositories>
        <repository>
            <id>aliyun</id>
            <name>Aliyun Maven Repository</name>
            <url>https://maven.aliyun.com/repository/public</url>
        </repository>
    </repositories>
</project>
```

---

## 四、公共模块创建

### 4.1 law-common 父 POM

**文件**: `law-common/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common</artifactId>
    <packaging>pom</packaging>

    <modules>
        <module>law-common-core</module>
        <module>law-common-redis</module>
        <module>law-common-security</module>
        <module>law-common-oss</module>
    </modules>
</project>
```

### 4.2 law-common-core 模块

**文件**: `law-common/law-common-core/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-common</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common-core</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>fastjson</artifactId>
        </dependency>
        <dependency>
            <groupId>com.github.xiaoymin</groupId>
            <artifactId>knife4j-openapi3-jakarta-spring-boot-starter</artifactId>
        </dependency>
    </dependencies>
</project>
```

**核心类**: 从原仓库 `law-ai-service` 提取

1. **Result.java** - 统一返回结果
  - 源位置: `law-ai-service/src/main/java/org/lawaiservice/result/Result.java`
  - 目标位置: `law-common/law-common-core/src/main/java/org/law/common/core/result/Result.java`
  - 修改包名: `org.lawaiservice.result` → `org.law.common.core.result`

2. **BaseException.java** - 基础异常类
  - 源位置: `law-ai-service/src/main/java/org/lawaiservice/exception/`
  - 目标位置: `law-common/law-common-core/src/main/java/org/law/common/core/exception/`

3. **GlobalExceptionHandler.java** - 全局异常处理
  - 源位置: `law-ai-service/src/main/java/org/lawaiservice/handler/`
  - 目标位置: `law-common/law-common-core/src/main/java/org/law/common/core/exception/`

4. **实体类** - 从 law-ai-pojo 提取
  - 源位置: `law-ai-pojo/src/main/java/org/lawpojo/entity/`
  - 目标位置: `law-common/law-common-core/src/main/java/org/law/common/core/entity/`

### 4.3 law-common-redis 模块

**文件**: `law-common/law-common-redis/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-common</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common-redis</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-core</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
    </dependencies>
</project>
```

**核心类**: 从原仓库提取 Redis 相关配置和工具类

### 4.4 law-common-security 模块

**文件**: `law-common/law-common-security/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-common</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common-security</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-core</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-redis</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt</artifactId>
        </dependency>
    </dependencies>
</project>
```

**核心类**: 从原仓库提取 JWT 相关类

- `JwtUtil.java` - JWT 工具类
- `JwtInterceptor.java` - JWT 拦截器
- `RequireLogin.java` - 登录注解
- `SecurityConfig.java` - 安全配置

### 4.5 law-common-oss 模块

**文件**: `law-common/law-common-oss/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-common</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common-oss</artifactId>

    <dependencies>
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-core</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>
        <dependency>
            <groupId>com.aliyun.oss</groupId>
            <artifactId>aliyun-sdk-oss</artifactId>
        </dependency>
    </dependencies>
</project>
```

**核心类**: 从原仓库提取 OSS 相关类

- `OssConfig.java` - OSS 配置
- `OssUtil.java` - OSS 工具类

---

## 五、网关服务创建

### 5.1 pom.xml

**文件**: `law-gateway/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-gateway</artifactId>

    <dependencies>
        <!-- Spring Cloud Gateway -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-gateway</artifactId>
        </dependency>

        <!-- Nacos Discovery -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
        </dependency>

        <!-- LoadBalancer -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-loadbalancer</artifactId>
        </dependency>

        <!-- JWT -->
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt</artifactId>
        </dependency>

        <!-- Redis Reactive -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis-reactive</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 5.2 启动类

**文件**: `law-gateway/src/main/java/org/law/gateway/GatewayApplication.java`

```java
package org.law.gateway;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;

@SpringBootApplication
@EnableDiscoveryClient
public class GatewayApplication {
    public static void main(String[] args) {
        SpringApplication.run(GatewayApplication.class, args);
    }
}
```

### 5.3 配置文件

**文件**: `law-gateway/src/main/resources/application.yml`

```yaml
server:
  port: 80

spring:
  application:
    name: law-gateway
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
    gateway:
      discovery:
        locator:
          enabled: false
      routes:
        # 用户服务路由
        - id: user-service
          uri: lb://law-user-service
          predicates:
            - Path=/api/user/**, /api/admin/user/**
          filters:
            - StripPrefix=0

        # 法典服务路由
        - id: law-service
          uri: lb://law-law-service
          predicates:
            - Path=/api/law/**, /api/admin/law/**
          filters:
            - StripPrefix=0

        # AI服务路由
        - id: ai-service
          uri: lb://law-ai-service
          predicates:
            - Path=/api/ai/**
          filters:
            - StripPrefix=0

        # 通用服务路由
        - id: common-service
          uri: lb://law-common-service
          predicates:
            - Path=/api/carousel/**, /api/upload/**, /api/workspace/**
          filters:
            - StripPrefix=0

      # 全局跨域配置
      globalcors:
        cors-configurations:
          '[/**]':
            allowedOrigins: "*"
            allowedMethods: "*"
            allowedHeaders: "*"

  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: 0

# 白名单路径（不需要鉴权）
gateway:
  whitelist:
    - /api/user/login
    - /api/user/register
    - /api/user/send-code
    - /api/carousel/list
    - /api/law/books
    - /api/law/cases

# JWT 配置
law:
  jwt:
    admin-secret-key: ${JWT_SECRET:lawai}
```

### 5.4 鉴权过滤器

**文件**: `law-gateway/src/main/java/org/law/gateway/filter/AuthGlobalFilter.java`

```java
package org.law.gateway.filter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.List;

@Component
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    @Value("${gateway.whitelist:}")
    private List<String> whitelist;

    @Value("${law.jwt.admin-secret-key:lawai}")
    private String secretKey;

    private final AntPathMatcher pathMatcher = new AntPathMatcher();

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        // 检查是否在白名单中
        if (isWhitelist(path)) {
            return chain.filter(exchange);
        }

        // 获取Token
        String token = request.getHeaders().getFirst("token");
        if (token == null || token.isEmpty()) {
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }

        // 验证Token
        try {
            Claims claims = Jwts.parser()
                    .setSigningKey(secretKey)
                    .parseClaimsJws(token)
                    .getBody();

            // 将用户信息添加到请求头
            ServerHttpRequest mutableRequest = request.mutate()
                    .header("X-User-Id", claims.getSubject())
                    .build();

            return chain.filter(exchange.mutate().request(mutableRequest).build());
        } catch (Exception e) {
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }
    }

    private boolean isWhitelist(String path) {
        return whitelist.stream().anyMatch(pattern -> pathMatcher.match(pattern, path));
    }

    @Override
    public int getOrder() {
        return -100;
    }
}
```

### 5.5 Dockerfile

**文件**: `law-gateway/Dockerfile`

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/law-gateway-1.0.0-SNAPSHOT.jar app.jar
EXPOSE 80
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 六、用户服务创建

### 6.1 pom.xml

**文件**: `law-user-service/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-user-service</artifactId>

    <dependencies>
        <!-- 公共模块 -->
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-security</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>

        <!-- Nacos -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
        </dependency>
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
        </dependency>

        <!-- Spring Boot -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
        </dependency>

        <!-- MySQL -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Druid -->
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>druid-spring-boot-starter</artifactId>
        </dependency>

        <!-- PageHelper -->
        <dependency>
            <groupId>com.github.pagehelper</groupId>
            <artifactId>pagehelper-spring-boot-starter</artifactId>
        </dependency>

        <!-- Mail -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-mail</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>

        <!-- Feign -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-openfeign</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-loadbalancer</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 6.2 启动类

**文件**: `law-user-service/src/main/java/org/law/user/UserServiceApplication.java`

```java
package org.law.user;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@MapperScan("org.law.user.mapper")
@ComponentScan(basePackages = {"org.law.user", "org.law.common"})
public class UserServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(UserServiceApplication.class, args);
    }
}
```

### 6.3 配置文件

**文件**: `law-user-service/src/main/resources/bootstrap.yml`

```yaml
spring:
  application:
    name: law-user-service
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
      config:
        server-addr: ${NACOS_ADDR:localhost:8848}
        file-extension: yml
        group: DEFAULT_GROUP
```

**文件**: `law-user-service/src/main/resources/application.yml`

```yaml
server:
  port: 8081

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
    druid:
      initial-size: 5
      max-active: 20
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: 2

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: org.law.user.entity
  configuration:
    map-underscore-to-camel-case: true

logging:
  level:
    org.law.user.mapper: debug
```

### 6.4 代码迁移

从原仓库 `law-ai-service` 迁移用户相关代码：

| 原文件 | 目标文件 | 修改内容 |
|--------|----------|----------|
| `controller/UserController.java` | `law-user-service/.../controller/UserController.java` | 修改包名 |
| `controller/AdminUserController.java` | `law-user-service/.../controller/AdminUserController.java` | 修改包名 |
| `service/UserService.java` | `law-user-service/.../service/UserService.java` | 修改包名 |
| `service/EmailVerificationService.java` | `law-user-service/.../service/EmailVerificationService.java` | 修改包名 |
| `mapper/UserMapper.java` | `law-user-service/.../mapper/UserMapper.java` | 修改包名 |
| `mapper/UserMapper.xml` | `law-user-service/.../resources/mapper/UserMapper.xml` | 修改 namespace |
| `entity/User.java` | `law-user-service/.../entity/User.java` | 修改包名 |

### 6.5 Dockerfile

**文件**: `law-user-service/Dockerfile`

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/law-user-service-1.0.0-SNAPSHOT.jar app.jar
EXPOSE 8081
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 七、法典服务创建

### 7.1 pom.xml

**文件**: `law-law-service/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-law-service</artifactId>

    <dependencies>
        <!-- 公共模块 -->
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-security</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>

        <!-- Nacos -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
        </dependency>
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
        </dependency>

        <!-- Spring Boot -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
        </dependency>

        <!-- MySQL -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Druid -->
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>druid-spring-boot-starter</artifactId>
        </dependency>

        <!-- PageHelper -->
        <dependency>
            <groupId>com.github.pagehelper</groupId>
            <artifactId>pagehelper-spring-boot-starter</artifactId>
        </dependency>

        <!-- POI -->
        <dependency>
            <groupId>org.apache.poi</groupId>
            <artifactId>poi</artifactId>
            <version>5.2.3</version>
        </dependency>
        <dependency>
            <groupId>org.apache.poi</groupId>
            <artifactId>poi-ooxml</artifactId>
            <version>5.2.3</version>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>

        <!-- Feign -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-openfeign</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-loadbalancer</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 7.2 启动类

**文件**: `law-law-service/src/main/java/org/law/law/LawServiceApplication.java`

```java
package org.law.law;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@MapperScan("org.law.law.mapper")
@ComponentScan(basePackages = {"org.law.law", "org.law.common"})
public class LawServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(LawServiceApplication.class, args);
    }
}
```

### 7.3 配置文件

**文件**: `law-law-service/src/main/resources/bootstrap.yml`

```yaml
spring:
  application:
    name: law-law-service
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
      config:
        server-addr: ${NACOS_ADDR:localhost:8848}
        file-extension: yml
        group: DEFAULT_GROUP
```

**文件**: `law-law-service/src/main/resources/application.yml`

```yaml
server:
  port: 8082

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
    druid:
      initial-size: 5
      max-active: 20

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: org.law.law.entity
  configuration:
    map-underscore-to-camel-case: true

logging:
  level:
    org.law.law.mapper: debug
```

### 7.4 代码迁移

从原仓库迁移法典相关代码：

| 原文件 | 目标文件 |
|--------|----------|
| `controller/LawBookController.java` | `law-law-service/.../controller/admin/LawBookController.java` |
| `controller/LawArticleController.java` | `law-law-service/.../controller/admin/LawArticleController.java` |
| `controller/LawCaseController.java` | `law-law-service/.../controller/admin/LawCaseController.java` |
| `controller/LawTypeController.java` | `law-law-service/.../controller/admin/LawTypeController.java` |
| `service/LawBookService.java` | `law-law-service/.../service/LawBookService.java` |
| `service/LawArticleService.java` | `law-law-service/.../service/LawArticleService.java` |
| `service/LawCaseService.java` | `law-law-service/.../service/LawCaseService.java` |
| `service/LawTypeService.java` | `law-law-service/.../service/LawTypeService.java` |
| `mapper/LawBookMapper.java` | `law-law-service/.../mapper/LawBookMapper.java` |
| `mapper/*.xml` | `law-law-service/.../resources/mapper/*.xml` |

### 7.5 Feign 客户端（供 AI 服务调用）

**文件**: `law-law-service/src/main/java/org/law/law/feign/LawArticleFeignController.java`

```java
package org.law.law.feign;

import org.law.common.core.result.Result;
import org.law.law.service.LawArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
public class LawArticleFeignController {

    @Autowired
    private LawArticleService lawArticleService;

    @GetMapping("/feign/law/articles/search")
    public Result<List<String>> searchArticles(@RequestParam String keyword) {
        return Result.success(lawArticleService.searchByKeyword(keyword));
    }
}
```

### 7.6 Dockerfile

**文件**: `law-law-service/Dockerfile`

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/law-law-service-1.0.0-SNAPSHOT.jar app.jar
EXPOSE 8082
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 八、AI 服务改造

### 8.1 pom.xml 改造

**文件**: `law-ai-service/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-ai-service</artifactId>

    <dependencies>
        <!-- 公共模块 -->
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-security</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>

        <!-- Nacos -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
        </dependency>
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
        </dependency>

        <!-- Spring Boot -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-webflux</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- Spring AI -->
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-starter-model-openai</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-vector-store</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-advisors-vector-store</artifactId>
        </dependency>

        <!-- Milvus -->
        <dependency>
            <groupId>io.milvus</groupId>
            <artifactId>milvus-sdk-java</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
        </dependency>

        <!-- MySQL -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>

        <!-- Feign -->
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-openfeign</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.cloud</groupId>
            <artifactId>spring-cloud-starter-loadbalancer</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 8.2 启动类改造

**文件**: `law-ai-service/src/main/java/org/law/ai/AiServiceApplication.java`

```java
package org.law.ai;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients
@MapperScan("org.law.ai.mapper")
@ComponentScan(basePackages = {"org.law.ai", "org.law.common"})
public class AiServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(AiServiceApplication.class, args);
    }
}
```

### 8.3 配置文件

**文件**: `law-ai-service/src/main/resources/bootstrap.yml`

```yaml
spring:
  application:
    name: law-ai-service
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
      config:
        server-addr: ${NACOS_ADDR:localhost:8848}
        file-extension: yml
        group: DEFAULT_GROUP
```

**文件**: `law-ai-service/src/main/resources/application.yml`

```yaml
server:
  port: 8083

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
  ai:
    openai:
      base-url: https://dashscope.aliyuncs.com/compatible-mode
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: qwen3.5-flash
          temperature: 0.8
      embedding:
        options:
          model: text-embedding-v3
          dimensions: 1024
    vectorstore:
      milvus:
        databaseName: law_ai
        url: http://${MILVUS_HOST:localhost}:19530
        embeddingDimension: 1024
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: 2

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: org.law.ai.entity
  configuration:
    map-underscore-to-camel-case: true

logging:
  level:
    org.law.ai.mapper: debug
```

### 8.4 Feign 客户端（调用法典服务）

**文件**: `law-ai-service/src/main/java/org/law/ai/feign/LawServiceClient.java`

```java
package org.law.ai.feign;

import org.law.common.core.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

@FeignClient(name = "law-law-service")
public interface LawServiceClient {

    @GetMapping("/feign/law/articles/search")
    Result<List<String>> searchArticles(@RequestParam("keyword") String keyword);
}
```

### 8.5 代码迁移

从原仓库迁移 AI 相关代码，修改包名：

- `org.lawaiservice.controller.AIConsultController` → `org.law.ai.controller.AIConsultController`
- `org.lawaiservice.service.*` → `org.law.ai.service.*`
- `org.lawaiservice.mapper.*` → `org.law.ai.mapper.*`

### 8.6 Dockerfile

**文件**: `law-ai-service/Dockerfile`

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/law-ai-service-1.0.0-SNAPSHOT.jar app.jar
EXPOSE 8083
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 九、通用服务创建

### 9.1 pom.xml

**文件**: `law-common-service/pom.xml`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.law</groupId>
        <artifactId>law-consultant-microservice</artifactId>
        <version>1.0.0-SNAPSHOT</version>
    </parent>

    <artifactId>law-common-service</artifactId>

    <dependencies>
        <!-- 公共模块 -->
        <dependency>
            <groupId>org.law</groupId>
            <artifactId>law-common-oss</artifactId>
            <version>1.0.0-SNAPSHOT</version>
        </dependency>

        <!-- Nacos -->
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-discovery</artifactId>
        </dependency>
        <dependency>
            <groupId>com.alibaba.cloud</groupId>
            <artifactId>spring-cloud-starter-alibaba-nacos-config</artifactId>
        </dependency>

        <!-- Spring Boot -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>

        <!-- MyBatis -->
        <dependency>
            <groupId>org.mybatis.spring.boot</groupId>
            <artifactId>mybatis-spring-boot-starter</artifactId>
        </dependency>

        <!-- MySQL -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>

        <!-- Druid -->
        <dependency>
            <groupId>com.alibaba</groupId>
            <artifactId>druid-spring-boot-starter</artifactId>
        </dependency>

        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
        </dependency>
    </dependencies>

    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
</project>
```

### 9.2 启动类

**文件**: `law-common-service/src/main/java/org/law/common/service/CommonServiceApplication.java`

```java
package org.law.common.service;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@MapperScan("org.law.common.service.mapper")
@ComponentScan(basePackages = {"org.law.common.service", "org.law.common"})
public class CommonServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(CommonServiceApplication.class, args);
    }
}
```

### 9.3 配置文件

**文件**: `law-common-service/src/main/resources/bootstrap.yml`

```yaml
spring:
  application:
    name: law-common-service
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
      config:
        server-addr: ${NACOS_ADDR:localhost:8848}
        file-extension: yml
        group: DEFAULT_GROUP
```

**文件**: `law-common-service/src/main/resources/application.yml`

```yaml
server:
  port: 8084

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
    druid:
      initial-size: 5
      max-active: 20

mybatis:
  mapper-locations: classpath:mapper/*.xml
  type-aliases-package: org.law.common.service.entity
  configuration:
    map-underscore-to-camel-case: true

logging:
  level:
    org.law.common.service.mapper: debug

aliyun:
  oss:
    endpoint: oss-cn-beijing.aliyuncs.com
    bucket-name: ${BUCKET_NAME:test-bucket}
    access-key-id: ${OSS_ACCESS_KEY_ID:test-key}
    access-key-secret: ${OSS_ACCESS_KEY_SECRET:test-secret}
```

### 9.4 代码迁移

从原仓库迁移通用功能代码：

| 原文件 | 目标文件 |
|--------|----------|
| `controller/CarouselController.java` | `law-common-service/.../controller/CarouselController.java` |
| `controller/UploadController.java` | `law-common-service/.../controller/UploadController.java` |
| `controller/WorkSpcaeController.java` | `law-common-service/.../controller/WorkSpaceController.java` |
| `service/CarouselService.java` | `law-common-service/.../service/CarouselService.java` |
| `service/UploadService.java` | `law-common-service/.../service/UploadService.java` |
| `mapper/CarouselMapper.java` | `law-common-service/.../mapper/CarouselMapper.java` |

### 9.5 Dockerfile

**文件**: `law-common-service/Dockerfile`

```dockerfile
FROM eclipse-temurin:17-jre-alpine
WORKDIR /app
COPY target/law-common-service-1.0.0-SNAPSHOT.jar app.jar
EXPOSE 8084
ENTRYPOINT ["java", "-jar", "app.jar"]
```

---

## 十、Nacos 配置

### 10.1 Nacos 3.2.1 重要说明

**版本特性**：
- Nacos 3.x 需要 Java 17+ 运行环境
- 增强了 gRPC 协议支持，端口 9848（客户端 gRPC）和 9849（服务端 gRPC）
- 优化了配置中心和服务发现的性能
- 提供了更好的集群管理能力

**兼容性说明**：
- Spring Cloud Alibaba 2023.0.1.2 与 Nacos 3.2.1 完全兼容
- 客户端配置方式保持不变，但建议使用最新的 spring-cloud-starter-alibaba-nacos-* 依赖

**端口说明**：
- 8848: HTTP 端口（控制台和 API）
- 9848: 客户端 gRPC 端口（服务注册发现、配置监听）
- 9849: 服务端 gRPC 端口（集群同步）

### 10.2 创建 Nacos 配置

在 Nacos 控制台创建以下配置：

1. **common.yml** - 公共配置
2. **law-user-service.yml** - 用户服务配置
3. **law-law-service.yml** - 法典服务配置
4. **law-ai-service.yml** - AI 服务配置
5. **law-common-service.yml** - 通用服务配置

**配置步骤**：
1. 访问 http://localhost:8848/nacos
2. 使用 nacos/nacos 登录
3. 进入「配置管理」->「配置列表」
4. 点击「+」按钮创建配置
5. Data ID 格式：`{service-name}.yml`
6. Group 保持 `DEFAULT_GROUP`
7. 配置格式选择 `YAML`

### 10.3 公共配置 (common.yml)

```yaml
# 公共配置
spring:
  datasource:
    druid:
      initial-size: 5
      max-active: 20
      min-idle: 5
      max-wait: 60000

mybatis:
  configuration:
    map-underscore-to-camel-case: true

logging:
  level:
    root: INFO
```

### 10.4 用户服务配置 (law-user-service.yml)

```yaml
server:
  port: 8081

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}

law:
  jwt:
    admin-secret-key: ${JWT_SECRET:lawai}
    admin-ttl: 864000000
    admin-token-name: token
```

### 10.5 法典服务配置 (law-law-service.yml)

```yaml
server:
  port: 8082

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
```

### 10.6 AI 服务配置 (law-ai-service.yml)

```yaml
server:
  port: 8083

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
  ai:
    openai:
      api-key: ${OPENAI_API_KEY}
    vectorstore:
      milvus:
        url: http://${MILVUS_HOST:localhost}:19530
```

### 10.7 通用服务配置 (law-common-service.yml)

```yaml
server:
  port: 8084

spring:
  datasource:
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}

aliyun:
  oss:
    endpoint: oss-cn-beijing.aliyuncs.com
    bucket-name: ${BUCKET_NAME}
    access-key-id: ${OSS_ACCESS_KEY_ID}
    access-key-secret: ${OSS_ACCESS_KEY_SECRET}
```

---

## 十一、Docker 部署配置

### 11.1 docker-compose.yml

**文件**: `law-consultant-microservice/docker-compose.yml`

```yaml
version: '3.8'

services:
  # Nacos 注册中心
  nacos:
    image: nacos/nacos-server:v3.2.1
    container_name: nacos
    environment:
      - MODE=standalone
      - SPRING_DATASOURCE_PLATFORM=mysql
      - MYSQL_SERVICE_HOST=${DB_HOST:mysql}
      - MYSQL_SERVICE_PORT=3306
      - MYSQL_SERVICE_USER=root
      - MYSQL_SERVICE_PASSWORD=${DB_PASSWORD}
      - MYSQL_SERVICE_DB_NAME=nacos
    ports:
      - "8848:8848"
      - "9848:9848"
      - "9849:9849"
    depends_on:
      - mysql
    networks:
      - law-network

  # MySQL 数据库
  mysql:
    image: mysql:8.0
    container_name: law-mysql
    environment:
      - MYSQL_ROOT_PASSWORD=${DB_PASSWORD}
      - MYSQL_DATABASE=nacos
    ports:
      - "3306:3306"
    volumes:
      - mysql-data:/var/lib/mysql
      - ./sql:/docker-entrypoint-initdb.d
    networks:
      - law-network

  # Redis
  redis:
    image: redis:7-alpine
    container_name: law-redis
    ports:
      - "6379:6379"
    networks:
      - law-network

  # Milvus 向量数据库
  etcd:
    image: quay.io/coreos/etcd:v3.5.5
    container_name: milvus-etcd
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
      - ETCD_SNAPSHOT_COUNT=50000
    volumes:
      - etcd-data:/etcd
    command: etcd -advertise-client-urls=http://127.0.0.1:2379 -listen-client-urls http://0.0.0.0:2379 --data-dir /etcd
    networks:
      - law-network

  minio:
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    container_name: milvus-minio
    environment:
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
    ports:
      - "9001:9001"
      - "9000:9000"
    volumes:
      - minio-data:/minio_data
    command: minio server /minio_data --console-address ":9001"
    networks:
      - law-network

  milvus-standalone:
    image: milvusdb/milvus:v2.4.5
    container_name: milvus-standalone
    environment:
      - ETCD_ENDPOINTS=etcd:2379
      - MINIO_ADDRESS=minio:9000
    command: ["milvus", "run", "standalone"]
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    networks:
      - law-network

  # API 网关
  law-gateway:
    build: ./law-gateway
    container_name: law-gateway
    ports:
      - "80:80"
    environment:
      - NACOS_ADDR=nacos:8848
      - REDIS_HOST=redis
    depends_on:
      - nacos
      - redis
    networks:
      - law-network

  # 用户服务
  law-user-service:
    build: ./law-user-service
    container_name: law-user-service
    environment:
      - NACOS_ADDR=nacos:8848
      - DB_HOST=mysql
      - REDIS_HOST=redis
    depends_on:
      - nacos
      - mysql
      - redis
    networks:
      - law-network

  # 法典服务
  law-law-service:
    build: ./law-law-service
    container_name: law-law-service
    environment:
      - NACOS_ADDR=nacos:8848
      - DB_HOST=mysql
    depends_on:
      - nacos
      - mysql
    networks:
      - law-network

  # AI 服务
  law-ai-service:
    build: ./law-ai-service
    container_name: law-ai-service
    environment:
      - NACOS_ADDR=nacos:8848
      - DB_HOST=mysql
      - MILVUS_HOST=milvus-standalone
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    depends_on:
      - nacos
      - mysql
      - milvus-standalone
    networks:
      - law-network

  # 通用服务
  law-common-service:
    build: ./law-common-service
    container_name: law-common-service
    environment:
      - NACOS_ADDR=nacos:8848
      - DB_HOST=mysql
      - OSS_ACCESS_KEY_ID=${OSS_ACCESS_KEY_ID}
      - OSS_ACCESS_KEY_SECRET=${OSS_ACCESS_KEY_SECRET}
    depends_on:
      - nacos
      - mysql
    networks:
      - law-network

volumes:
  mysql-data:
  etcd-data:
  minio-data:

networks:
  law-network:
    driver: bridge
```

---

## 十二、测试验证

### 12.1 本地开发测试

```bash
# 1. 启动基础设施
docker-compose up -d mysql redis nacos

# 2. 启动 Milvus（如果需要 AI 功能）
docker-compose up -d etcd minio milvus-standalone

# 3. 编译项目
mvn clean package -DskipTests

# 4. 依次启动各服务
cd law-gateway && mvn spring-boot:run
cd law-user-service && mvn spring-boot:run
cd law-law-service && mvn spring-boot:run
cd law-ai-service && mvn spring-boot:run
cd law-common-service && mvn spring-boot:run
```

### 12.2 验证清单

- [ ] Nacos 控制台能看到所有服务注册
- [ ] 通过网关访问用户服务接口
- [ ] 通过网关访问法典服务接口
- [ ] 通过网关访问 AI 服务接口
- [ ] 通过网关访问通用服务接口
- [ ] AI 服务能调用法典服务获取法律知识
- [ ] 前端对接网关地址正常工作

### 12.3 常见问题

1. **服务注册失败**: 检查 Nacos 地址配置是否正确
2. **数据库连接失败**: 检查数据库配置和网络连通性
3. **Feign 调用失败**: 检查服务名是否正确，服务是否已注册
4. **CORS 跨域问题**: 检查网关跨域配置

### 12.4 Nacos 3.2.1 特别注意事项

**1. Java 版本要求**
```bash
# 确认 Java 版本为 17+
java -version
```

**2. 端口开放**
确保以下端口未被占用且已开放：
- 8848: HTTP 控制台和 API
- 9848: 客户端 gRPC（必须）
- 9849: 服务端 gRPC（集群模式需要）

**3. 启动参数优化**
```bash
# Nacos 3.x 单机模式启动（推荐）
./startup.sh -m standalone

# 如果需要调整 JVM 参数
export JAVA_OPTS="-Xms512m -Xmx2g -Xmn256m"
./startup.sh -m standalone
```

**4. 配置文件格式**
Nacos 3.x 支持多种配置格式，推荐使用 YAML：
- Data ID: `law-user-service.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`

**5. 客户端依赖版本**
确保使用兼容的 Spring Cloud Alibaba 版本：
```xml
<spring-cloud-alibaba.version>2023.0.1.2</spring-cloud-alibaba.version>
```

**6. 配置监听问题**
如果配置更新后未生效，检查：
- bootstrap.yml 中是否配置了 Nacos Config
- spring.cloud.nacos.config.file-extension 是否为 yml
- 服务是否正确重启或使用了 @RefreshScope

**7. Docker 部署注意事项**
```yaml
# docker-compose.yml 中必须暴露 gRPC 端口
ports:
  - "8848:8848"  # HTTP
  - "9848:9848"  # Client gRPC
  - "9849:9849"  # Server gRPC
```

**8. 数据库初始化**
Nacos 3.x 使用的数据库脚本位置：
```bash
# SQL 脚本位置
nacos/conf/mysql-schema.sql

# 执行初始化
mysql -u root -p nacos < nacos/conf/mysql-schema.sql
```

---

## 附录：包名对照表

| 原包名 | 新包名 |
|--------|--------|
| `org.lawpojo` | `org.law.common.core.entity` |
| `org.lawaiservice.result` | `org.law.common.core.result` |
| `org.lawaiservice.exception` | `org.law.common.core.exception` |
| `org.lawaiservice.utils` | `org.law.common.core.utils` |
| `org.lawaiservice.config` | `org.law.common.core.config` |
| `org.lawaiservice.interceptor` | `org.law.common.security.interceptor` |
| `org.lawaiservice.annotation` | `org.law.common.security.annotation` |
| `org.lawaiservice.controller` (用户) | `org.law.user.controller` |
| `org.lawaiservice.controller` (法典) | `org.law.law.controller` |
| `org.lawaiservice.controller` (AI) | `org.law.ai.controller` |
| `org.lawaiservice.controller` (通用) | `org.law.common.service.controller` |

---

## 十三、代码迁移详细步骤

### 13.1 迁移前准备

1. **备份原仓库**
   ```bash
   # 在原仓库目录执行
   cd D:\code\java\law-consultant-project
   git add .
   git commit -m "备份：微服务改造前的代码快照"
   git tag pre-microservice
   ```

2. **分析原仓库代码结构**
   ```bash
   # 查看所有 Java 文件
   find law-ai-service/src/main/java -name "*.java" | sort
   
   # 查看所有 Mapper XML 文件
   find law-ai-service/src/main/resources/mapper -name "*.xml"
   
   # 查看 law-ai-pojo 中的实体类
   find law-ai-pojo/src/main/java -name "*.java"
   ```

### 13.2 公共模块代码提取

#### 步骤 1：提取 Result 类

```bash
# 1. 复制文件
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\result\Result.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\result\Result.java

# 2. 修改包名（使用 IDE 或 sed）
# 将 package org.lawaiservice.result; 改为 package org.law.common.core.result;
```

**手动修改步骤**：
1. 用 IDE 打开 `Result.java`
2. 修改第一行：`package org.lawaiservice.result;` → `package org.law.common.core.result;`
3. 保存文件

#### 步骤 2：提取异常类

```bash
# 复制异常相关文件
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\exception\*.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\exception\

# 如果有 handler 目录
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\handler\*.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\exception\
```

**修改包名**：
- `org.lawaiservice.exception` → `org.law.common.core.exception`
- `org.lawaiservice.handler` → `org.law.common.core.exception`

#### 步骤 3：提取实体类

```bash
# 从 law-ai-pojo 提取实体类
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\*.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\entity\

# 从 law-ai-pojo 提取 DTO
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\dto\*.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\dto\

# 从 law-ai-pojo 提取 VO
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\vo\*.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-core\src\main\java\org\law\common\core\vo\
```

**修改包名**：
- `org.lawpojo.entity` → `org.law.common.core.entity`
- `org.lawpojo.dto` → `org.law.common.core.dto`
- `org.lawpojo.vo` → `org.law.common.core.vo`

#### 步骤 4：提取 JWT 工具类

```bash
# 复制 JWT 相关文件
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\utils\JwtUtil.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-security\src\main\java\org\law\common\security\utils\JwtUtil.java

# 复制拦截器
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\interceptor\JwtInterceptor.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-security\src\main\java\org\law\common\security\interceptor\JwtInterceptor.java

# 复制注解
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\annotation\RequireLogin.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-security\src\main\java\org\law\common\security\annotation\RequireLogin.java

# 复制配置类
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\config\WebMvcConfig.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-security\src\main\java\org\law\common\security\config\SecurityConfig.java
```

**修改包名**：
- `org.lawaiservice.utils` → `org.law.common.security.utils`
- `org.lawaiservice.interceptor` → `org.law.common.security.interceptor`
- `org.lawaiservice.annotation` → `org.law.common.security.annotation`
- `org.lawaiservice.config` → `org.law.common.security.config`

#### 步骤 5：提取 OSS 工具类

```bash
# 复制 OSS 相关文件
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\utils\OssUtil.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-oss\src\main\java\org\law\common\oss\utils\OssUtil.java

# 复制配置类（如果有）
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\config\OssConfig.java \
   D:\code\java\law-consultant-microservice\law-common\law-common-oss\src\main\java\org\law\common\oss\config\OssConfig.java
```

### 13.3 用户服务代码迁移

```bash
# 创建目标目录
mkdir -p D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\{controller,service,mapper,entity,dto,vo}
mkdir -p D:\code\java\law-consultant-microservice\law-user-service\src\main\resources\mapper

# 复制用户相关 Controller
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\UserController.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\controller\UserController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\AdminUserController.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\controller\AdminUserController.java

# 复制用户相关 Service
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\UserService.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\service\UserService.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\EmailVerificationService.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\service\EmailVerificationService.java

# 复制用户相关 Mapper
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\UserMapper.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\mapper\UserMapper.java

# 复制 Mapper XML
cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\UserMapper.xml \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\resources\mapper\UserMapper.xml

# 复制用户实体类
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\User.java \
   D:\code\java\law-consultant-microservice\law-user-service\src\main\java\org\law\user\entity\User.java
```

**修改包名**：
- `org.lawaiservice.controller` → `org.law.user.controller`
- `org.lawaiservice.service` → `org.law.user.service`
- `org.lawaiservice.mapper` → `org.law.user.mapper`
- `org.lawpojo.entity` → `org.law.user.entity`

**修改 Mapper XML namespace**：
```xml
<!-- 原来 -->
<mapper namespace="org.lawaiservice.mapper.UserMapper">

<!-- 修改为 -->
<mapper namespace="org.law.user.mapper.UserMapper">
```

### 13.4 法典服务代码迁移

```bash
# 创建目标目录
mkdir -p D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\{controller/admin,controller/user,service,mapper,entity}
mkdir -p D:\code\java\law-consultant-microservice\law-law-service\src\main\resources\mapper

# 复制法典相关 Controller
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\LawBookController.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\controller\admin\LawBookController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\LawArticleController.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\controller\admin\LawArticleController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\LawCaseController.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\controller\admin\LawCaseController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\LawTypeController.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\controller\admin\LawTypeController.java

# 复制法典相关 Service
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\LawBookService.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\service\LawBookService.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\LawArticleService.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\service\LawArticleService.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\LawCaseService.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\service\LawCaseService.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\LawTypeService.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\service\LawTypeService.java

# 复制法典相关 Mapper
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\LawBookMapper.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\mapper\LawBookMapper.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\LawArticleMapper.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\mapper\LawArticleMapper.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\LawCaseMapper.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\mapper\LawCaseMapper.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\LawTypeMapper.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\mapper\LawTypeMapper.java

# 复制 Mapper XML
cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\LawBookMapper.xml \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\resources\mapper\

cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\LawArticleMapper.xml \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\resources\mapper\

cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\LawCaseMapper.xml \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\resources\mapper\

cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\LawTypeMapper.xml \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\resources\mapper\

# 复制实体类
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\LawBook.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\entity\

cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\LawArticle.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\entity\

cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\LawCase.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\entity\

cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\LawType.java \
   D:\code\java\law-consultant-microservice\law-law-service\src\main\java\org\law\law\entity\
```

**修改 Mapper XML namespace**：
```xml
<!-- LawBookMapper.xml -->
<mapper namespace="org.law.law.mapper.LawBookMapper">

<!-- LawArticleMapper.xml -->
<mapper namespace="org.law.law.mapper.LawArticleMapper">

<!-- LawCaseMapper.xml -->
<mapper namespace="org.law.law.mapper.LawCaseMapper">

<!-- LawTypeMapper.xml -->
<mapper namespace="org.law.law.mapper.LawTypeMapper">
```

### 13.5 AI 服务代码迁移

```bash
# 创建目标目录
mkdir -p D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\{controller,service,feign,mapper,entity}
mkdir -p D:\code\java\law-consultant-microservice\law-ai-service\src\main\resources\mapper

# 复制 AI 相关 Controller
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\AIConsultController.java \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\controller\AIConsultController.java

# 复制 AI 相关 Service
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\AIConsultService.java \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\service\AIConsultService.java

# 复制其他 AI 相关 Service（根据实际情况）
# cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\*.java \
#    D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\service\

# 复制 AI 相关 Mapper
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\AiConsultationMapper.java \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\mapper\AiConsultationMapper.java

# 复制 Mapper XML
cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\AiConsultationMapper.xml \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\resources\mapper\

# 复制实体类
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\AiConsultation.java \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\entity\

cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\ConversationHistory.java \
   D:\code\java\law-consultant-microservice\law-ai-service\src\main\java\org\law\ai\entity\
```

**修改 Mapper XML namespace**：
```xml
<mapper namespace="org.law.ai.mapper.AiConsultationMapper">
```

### 13.6 通用服务代码迁移

```bash
# 创建目标目录
mkdir -p D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\{controller,service,mapper,entity}
mkdir -p D:\code\java\law-consultant-microservice\law-common-service\src\main\resources\mapper

# 复制轮播图相关代码
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\CarouselController.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\controller\CarouselController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\CarouselService.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\service\CarouselService.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\mapper\CarouselMapper.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\mapper\CarouselMapper.java

# 复制文件上传相关代码
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\UploadController.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\controller\UploadController.java

cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\service\UploadService.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\service\UploadService.java

# 复制工作台相关代码
cp D:\code\java\law-consultant-project\law-ai-service\src\main\java\org\lawaiservice\controller\WorkSpcaeController.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\controller\WorkSpaceController.java

# 复制 Mapper XML
cp D:\code\java\law-consultant-project\law-ai-service\src\main\resources\mapper\CarouselMapper.xml \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\resources\mapper\

# 复制实体类
cp D:\code\java\law-consultant-project\law-ai-pojo\src\main\java\org\lawpojo\entity\Carousel.java \
   D:\code\java\law-consultant-microservice\law-common-service\src\main\java\org\law\common\service\entity\
```

**修改 Mapper XML namespace**：
```xml
<mapper namespace="org.law.common.service.mapper.CarouselMapper">
```

### 13.7 批量修改包名脚本

创建一个脚本来批量修改包名：

**文件**: `migrate-packages.sh`

```bash
#!/bin/bash

# 批量修改包名的脚本
# 用法: ./migrate-packages.sh <目录> <原包名> <新包名>

DIR=$1
OLD_PACKAGE=$2
NEW_PACKAGE=$3

# 将包名中的点替换为斜杠
OLD_PATH=${OLD_PACKAGE//\./\/}
NEW_PATH=${NEW_PACKAGE//\./\/}

# 修改 Java 文件中的包名和 import
find $DIR -name "*.java" -exec sed -i "s/package $OLD_PACKAGE/package $NEW_PACKAGE/g" {} \;
find $DIR -name "*.java" -exec sed -i "s/import $OLD_PACKAGE/import $NEW_PACKAGE/g" {} \;

# 修改 Mapper XML 中的 namespace
find $DIR -name "*.xml" -exec sed -i "s/$OLD_PACKAGE/$NEW_PACKAGE/g" {} \;

echo "修改完成: $OLD_PACKAGE -> $NEW_PACKAGE"
```

**使用示例**：
```bash
# 修改用户服务的包名
./migrate-packages.sh law-user-service/src org.lawaiservice org.law.user
./migrate-packages.sh law-user-service/src org.lawpojo org.law.user

# 修改法典服务的包名
./migrate-packages.sh law-law-service/src org.lawaiservice org.law.law
./migrate-packages.sh law-law-service/src org.lawpojo org.law.law

# 修改 AI 服务的包名
./migrate-packages.sh law-ai-service/src org.lawaiservice org.law.ai
./migrate-packages.sh law-ai-service/src org.lawpojo org.law.ai

# 修改通用服务的包名
./migrate-packages.sh law-common-service/src org.lawaiservice org.law.common.service
./migrate-packages.sh law-common-service/src org.lawpojo org.law.common.service
```

---

## 十四、数据库迁移详细步骤

### 14.1 数据库现状分析

原数据库 `law_consultation` 包含以下表：

```sql
-- 查看原数据库表结构
USE law_consultation;
SHOW TABLES;

-- 预期的表列表
-- user                    - 用户表
-- law_book               - 法典表
-- law_article            - 法条表
-- law_case               - 案例表
-- law_type               - 法律类型表
-- case_collection        - 案例收藏表
-- ai_consultation        - AI咨询表
-- conversation_history   - 对话历史表
-- carousel               - 轮播图表
-- activities             - 活动表
```

### 14.2 共享数据库配置

由于采用共享数据库策略，所有微服务连接同一个数据库 `law_consultation`。

**配置要点**：

1. **所有服务使用相同的数据库连接**
   ```yaml
   spring:
     datasource:
       driver-class-name: com.mysql.cj.jdbc.Driver
       url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8
       username: ${DB_USERNAME:root}
       password: ${DB_PASSWORD:root}
   ```

2. **各服务只访问自己负责的表**
  - 用户服务：只访问 `user` 表
  - 法典服务：只访问 `law_book`, `law_article`, `law_case`, `law_type`, `case_collection` 表
  - AI 服务：只访问 `ai_consultation`, `conversation_history` 表
  - 通用服务：只访问 `carousel`, `activities` 表

### 14.3 数据库权限控制（可选）

如果需要更严格的权限控制，可以为每个服务创建独立的数据库用户：

```sql
-- 创建用户服务专用用户
CREATE USER 'law_user_svc'@'%' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.user TO 'law_user_svc'@'%';

-- 创建法典服务专用用户
CREATE USER 'law_law_svc'@'%' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.law_book TO 'law_law_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.law_article TO 'law_law_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.law_case TO 'law_law_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.law_type TO 'law_law_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.case_collection TO 'law_law_svc'@'%';

-- 创建 AI 服务专用用户
CREATE USER 'law_ai_svc'@'%' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.ai_consultation TO 'law_ai_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.conversation_history TO 'law_ai_svc'@'%';

-- 创建通用服务专用用户
CREATE USER 'law_common_svc'@'%' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.carousel TO 'law_common_svc'@'%';
GRANT SELECT, INSERT, UPDATE, DELETE ON law_consultation.activities TO 'law_common_svc'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
```

### 14.4 数据库表结构备份

```bash
# 备份原数据库结构
mysqldump -u root -p --no-data law_consultation > law_consultation_schema.sql

# 备份原数据库数据
mysqldump -u root -p law_consultation > law_consultation_data.sql

# 完整备份（结构 + 数据）
mysqldump -u root -p law_consultation > law_consultation_full.sql
```

### 14.5 数据库表归属对照表

| 表名 | 所属服务 | 说明 |
|------|----------|------|
| `user` | law-user-service | 用户信息 |
| `law_book` | law-law-service | 法典信息 |
| `law_article` | law-law-service | 法条信息 |
| `law_case` | law-law-service | 案例信息 |
| `law_type` | law-law-service | 法律类型 |
| `case_collection` | law-law-service | 案例收藏 |
| `ai_consultation` | law-ai-service | AI 咨询记录 |
| `conversation_history` | law-ai-service | 对话历史 |
| `carousel` | law-common-service | 轮播图 |
| `activities` | law-common-service | 活动信息 |

### 14.6 数据库迁移验证

迁移完成后，验证各服务能正常访问数据库：

```bash
# 1. 启动用户服务
cd law-user-service
mvn spring-boot:run

# 2. 测试用户服务数据库连接
curl http://localhost:8081/api/user/list

# 3. 启动法典服务
cd law-law-service
mvn spring-boot:run

# 4. 测试法典服务数据库连接
curl http://localhost:8082/api/law/books

# 5. 依次测试其他服务...
```

---

## 十五、Nacos 配置详细步骤

### 15.1 Nacos 安装与启动

#### Windows 安装

```bash
# 1. 下载 Nacos
# 访问 https://github.com/alibaba/nacos/releases
# 下载 nacos-server-2.3.0.zip

# 2. 解压到指定目录
# 例如: D:\nacos\nacos-server-2.3.0

# 3. 配置 Nacos 数据库
# 编辑 D:\nacos\nacos-server-2.3.0\conf\application.properties
```

**application.properties 关键配置**：
```properties
# 数据库配置
spring.datasource.platform=mysql
db.num=1
db.url.0=jdbc:mysql://localhost:3306/nacos?characterEncoding=utf8&connectTimeout=1000&socketTimeout=3000&autoReconnect=true&useUnicode=true&useSSL=false&serverTimezone=UTC
db.user.0=root
db.password.0=your_password

# 单机模式
# nacos.standalone=true (在 startup.cmd 中设置)
```

```bash
# 4. 创建 nacos 数据库
mysql -u root -p < D:\nacos\nacos-server-2.3.0\conf\mysql-schema.sql

# 5. 启动 Nacos（单机模式）
cd D:\nacos\nacos-server-2.3.0\bin
startup.cmd -m standalone

# 6. 访问 Nacos 控制台
# http://localhost:8848/nacos
# 默认账号: nacos
# 默认密码: nacos
```

#### Linux/Mac 安装

```bash
# 1. 下载
wget https://github.com/alibaba/nacos/releases/download/2.3.0/nacos-server-2.3.0.tar.gz

# 2. 解压
tar -xzf nacos-server-2.3.0.tar.gz
cd nacos

# 3. 配置数据库
vim conf/application.properties
# 修改数据库配置（同上）

# 4. 创建数据库
mysql -u root -p < conf/mysql-schema.sql

# 5. 启动
sh bin/startup.sh -m standalone

# 6. 访问
# http://localhost:8848/nacos
```

### 15.2 在 Nacos 控制台创建配置

#### 步骤 1：登录 Nacos 控制台

1. 打开浏览器访问 http://localhost:8848/nacos
2. 输入账号密码：nacos / nacos

#### 步骤 2：创建命名空间（可选）

1. 左侧菜单：命名空间
2. 点击"新建命名空间"
3. 填写信息：
  - 命名空间ID：dev
  - 命名空间名：开发环境
  - 描述：开发环境配置
4. 点击"确定"

#### 步骤 3：创建配置文件

1. 左侧菜单：配置管理 → 配置列表
2. 选择命名空间（如果创建了的话）
3. 点击"+"创建配置

**配置 1：公共配置 (common.yml)**

- Data ID: `common.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`
- 配置内容:

```yaml
# 公共配置
spring:
  datasource:
    druid:
      initial-size: 5
      max-active: 20
      min-idle: 5
      max-wait: 60000
      validation-query: SELECT 1
      test-while-idle: true
      test-on-borrow: false
      test-on-return: false

mybatis:
  configuration:
    map-underscore-to-camel-case: true
    log-impl: org.apache.ibatis.logging.stdout.StdOutImpl

logging:
  level:
    root: INFO
    org.law: DEBUG
```

**配置 2：用户服务配置 (law-user-service.yml)**

- Data ID: `law-user-service.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`
- 配置内容:

```yaml
server:
  port: 8081

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8&allowMultiQueries=true
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: 2
      password: ${REDIS_PASSWORD:}

law:
  jwt:
    admin-secret-key: ${JWT_SECRET:lawai}
    admin-ttl: 864000000
    admin-token-name: token

# 邮件配置
spring.mail:
  host: smtp.qq.com
  port: 465
  username: ${QQ_EMAIL:test@qq.com}
  password: ${EMAIL_AUTH_CODE:test-auth-code}
  properties:
    mail:
      smtp:
        auth: true
        ssl:
          enable: true
```

**配置 3：法典服务配置 (law-law-service.yml)**

- Data ID: `law-law-service.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`
- 配置内容:

```yaml
server:
  port: 8082

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8&allowMultiQueries=true
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
```

**配置 4：AI 服务配置 (law-ai-service.yml)**

- Data ID: `law-ai-service.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`
- 配置内容:

```yaml
server:
  port: 8083

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8&allowMultiQueries=true
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}
  ai:
    openai:
      base-url: https://dashscope.aliyuncs.com/compatible-mode
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: qwen3.5-flash
          temperature: 0.8
      embedding:
        options:
          model: text-embedding-v3
          dimensions: 1024
    vectorstore:
      milvus:
        databaseName: law_ai
        url: http://${MILVUS_HOST:localhost}:19530
        embeddingDimension: 1024
  data:
    redis:
      host: ${REDIS_HOST:localhost}
      port: ${REDIS_PORT:6379}
      database: 2
      password: ${REDIS_PASSWORD:}
```

**配置 5：通用服务配置 (law-common-service.yml)**

- Data ID: `law-common-service.yml`
- Group: `DEFAULT_GROUP`
- 配置格式: `YAML`
- 配置内容:

```yaml
server:
  port: 8084

spring:
  datasource:
    driver-class-name: com.mysql.cj.jdbc.Driver
    url: jdbc:mysql://${DB_HOST:localhost}:3306/law_consultation?serverTimezone=Asia/Shanghai&useUnicode=true&characterEncoding=utf-8&allowMultiQueries=true
    username: ${DB_USERNAME:root}
    password: ${DB_PASSWORD:root}

aliyun:
  oss:
    endpoint: oss-cn-beijing.aliyuncs.com
    bucket-name: ${BUCKET_NAME:test-bucket}
    access-key-id: ${OSS_ACCESS_KEY_ID:test-key}
    access-key-secret: ${OSS_ACCESS_KEY_SECRET:test-secret}
```

### 15.3 bootstrap.yml 配置详解

每个微服务都需要 `bootstrap.yml` 文件来连接 Nacos 配置中心：

```yaml
spring:
  application:
    name: law-user-service  # 服务名称，必须与 Nacos 中的 Data ID 对应
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}  # Nacos 服务地址
        namespace: ${NACOS_NAMESPACE:}              # 命名空间 ID（可选）
        group: DEFAULT_GROUP                        # 分组
      config:
        server-addr: ${NACOS_ADDR:localhost:8848}   # Nacos 配置中心地址
        namespace: ${NACOS_NAMESPACE:}              # 命名空间 ID（可选）
        group: DEFAULT_GROUP                        # 分组
        file-extension: yml                         # 配置文件扩展名
        shared-configs:                             # 共享配置
          - data-id: common.yml
            group: DEFAULT_GROUP
            refresh: true
```

**配置优先级**：
1. `application.yml`（本地配置）- 最高优先级
2. `law-user-service.yml`（Nacos 服务专属配置）
3. `common.yml`（Nacos 公共配置）- 最低优先级

### 15.4 Nacos 配置热更新

Nacos 支持配置热更新，修改配置后无需重启服务：

1. 在 Nacos 控制台修改配置
2. 点击"发布"
3. 服务会自动监听配置变化并刷新

**注意事项**：
- 需要添加 `@RefreshScope` 注解才能实现配置热更新
- 某些配置（如数据库连接池）可能需要重启才能生效

```java
@RestController
@RefreshScope  # 添加此注解
public class ConfigController {
    
    @Value("${my.custom.config}")
    private String customConfig;
    
    @GetMapping("/config")
    public String getConfig() {
        return customConfig;
    }
}
```

### 15.5 Nacos 配置导出与导入

#### 导出配置

1. Nacos 控制台 → 配置管理 → 配置列表
2. 勾选要导出的配置
3. 点击"导出"
4. 选择导出格式（ZIP 或 YAML）

#### 导入配置

1. Nacos 控制台 → 配置管理 → 配置列表
2. 点击"导入配置"
3. 选择文件上传
4. 选择目标命名空间和分组
5. 点击"确定"

### 15.6 Nacos 常见问题

**问题 1：服务注册失败**
```
解决方案：
1. 检查 Nacos 服务是否启动
2. 检查 bootstrap.yml 中的 server-addr 配置
3. 检查网络连通性
4. 检查防火墙设置
```

**问题 2：配置拉取失败**
```
解决方案：
1. 检查 Data ID 是否与 spring.application.name 一致
2. 检查 Group 是否匹配
3. 检查命名空间是否正确
4. 检查配置文件格式是否正确
```

**问题 3：配置热更新不生效**
```
解决方案：
1. 确保添加了 @RefreshScope 注解
2. 检查配置是否支持热更新
3. 查看日志是否有刷新记录
```

---

## 十六、服务间调用详细说明

### 16.1 Feign 基础概念

Feign 是一个声明式的 HTTP 客户端，用于微服务之间的调用。

**核心注解**：
- `@EnableFeignClients`：启用 Feign 客户端
- `@FeignClient`：声明 Feign 客户端接口

### 16.2 服务提供方（被调用方）

以法典服务为例，提供法条搜索接口供 AI 服务调用：

**步骤 1：创建 Feign 专用 Controller**

```java
package org.law.law.feign;

import org.law.common.core.result.Result;
import org.law.law.service.LawArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Feign 专用接口
 * 供其他微服务内部调用，不走网关鉴权
 */
@RestController
public class LawArticleFeignController {

    @Autowired
    private LawArticleService lawArticleService;

    /**
     * 搜索法条（内部接口）
     */
    @GetMapping("/feign/law/articles/search")
    public Result<List<String>> searchArticles(@RequestParam String keyword) {
        List<String> results = lawArticleService.searchByKeyword(keyword);
        return Result.success(results);
    }

    /**
     * 获取法条详情（内部接口）
     */
    @GetMapping("/feign/law/articles/detail")
    public Result<Object> getArticleDetail(@RequestParam Long id) {
        Object detail = lawArticleService.getById(id);
        return Result.success(detail);
    }
}
```

**步骤 2：确保服务已注册到 Nacos**

```yaml
# law-law-service/src/main/resources/bootstrap.yml
spring:
  application:
    name: law-law-service  # 服务名称
  cloud:
    nacos:
      discovery:
        server-addr: ${NACOS_ADDR:localhost:8848}
```

### 16.3 服务消费方（调用方）

以 AI 服务为例，调用法典服务获取法律知识：

**步骤 1：启用 Feign 客户端**

```java
package org.law.ai;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.cloud.openfeign.EnableFeignClients;
import org.springframework.context.annotation.ComponentScan;

@SpringBootApplication
@EnableDiscoveryClient
@EnableFeignClients  # 启用 Feign 客户端
@MapperScan("org.law.ai.mapper")
@ComponentScan(basePackages = {"org.law.ai", "org.law.common"})
public class AiServiceApplication {
    public static void main(String[] args) {
        SpringApplication.run(AiServiceApplication.class, args);
    }
}
```

**步骤 2：创建 Feign 客户端接口**

```java
package org.law.ai.feign;

import org.law.common.core.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;

import java.util.List;

/**
 * 法典服务 Feign 客户端
 * name: 对应服务提供方的 spring.application.name
 */
@FeignClient(name = "law-law-service")
public interface LawServiceClient {

    /**
     * 搜索法条
     */
    @GetMapping("/feign/law/articles/search")
    Result<List<String>> searchArticles(@RequestParam("keyword") String keyword);

    /**
     * 获取法条详情
     */
    @GetMapping("/feign/law/articles/detail")
    Result<Object> getArticleDetail(@RequestParam("id") Long id);
}
```

**步骤 3：在 Service 中使用 Feign 客户端**

```java
package org.law.ai.service;

import org.law.ai.feign.LawServiceClient;
import org.law.common.core.result.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;

@Service
public class AIConsultService {

    @Autowired
    private LawServiceClient lawServiceClient;

    /**
     * 处理用户咨询
     */
    public String consult(String question) {
        // 1. 从法典服务搜索相关法条
        Result<List<String>> searchResult = lawServiceClient.searchArticles(question);
        
        if (searchResult.getCode() == 200) {
            List<String> relatedArticles = searchResult.getData();
            
            // 2. 构建上下文
            StringBuilder context = new StringBuilder();
            context.append("相关法律条文：\n");
            for (String article : relatedArticles) {
                context.append("- ").append(article).append("\n");
            }
            
            // 3. 调用 AI 模型
            String prompt = context.toString() + "\n用户问题：" + question;
            return callAiModel(prompt);
        }
        
        return "抱歉，无法获取相关法律信息";
    }

    private String callAiModel(String prompt) {
        // 调用 Spring AI 的代码
        // ...
        return "AI 回答";
    }
}
```

### 16.4 Feign 配置详解

#### 添加 Feign 依赖

```xml
<!-- 在消费方的 pom.xml 中添加 -->
<dependencies>
    <!-- Feign -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-openfeign</artifactId>
    </dependency>
    
    <!-- LoadBalancer（必需） -->
    <dependency>
        <groupId>org.springframework.cloud</groupId>
        <artifactId>spring-cloud-starter-loadbalancer</artifactId>
    </dependency>
</dependencies>
```

#### Feign 超时配置

```yaml
# 在消费方的 application.yml 中配置
spring:
  cloud:
    openfeign:
      client:
        config:
          default:
            connectTimeout: 5000  # 连接超时（毫秒）
            readTimeout: 10000    # 读取超时（毫秒）
          law-law-service:        # 针对特定服务的配置
            connectTimeout: 3000
            readTimeout: 5000
```

#### Feign 日志配置

```yaml
# 在消费方的 application.yml 中配置
logging:
  level:
    org.law.ai.feign: DEBUG  # Feign 客户端接口的包名
```

```java
// 创建 Feign 日志配置类
package org.law.ai.config;

import feign.Logger;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class FeignConfig {

    @Bean
    Logger.Level feignLoggerLevel() {
        return Logger.Level.FULL;  // 完整日志
    }
}
```

### 16.5 Feign 错误处理

```java
package org.law.ai.feign;

import feign.hystrix.FallbackFactory;
import lombok.extern.slf4j.Slf4j;
import org.law.common.core.result.Result;
import org.springframework.cloud.openfeign.FallbackFactory;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * Feign 降级工厂
 */
@Component
@Slf4j
public class LawServiceFallbackFactory implements FallbackFactory<LawServiceClient> {

    @Override
    public LawServiceClient create(Throwable cause) {
        log.error("法典服务调用失败", cause);
        
        return new LawServiceClient() {
            @Override
            public Result<List<String>> searchArticles(String keyword) {
                return Result.error("法典服务暂时不可用，请稍后重试");
            }

            @Override
            public Result<Object> getArticleDetail(Long id) {
                return Result.error("法典服务暂时不可用，请稍后重试");
            }
        };
    }
}
```

**在 Feign 客户端中指定降级工厂**：

```java
@FeignClient(name = "law-law-service", fallbackFactory = LawServiceFallbackFactory.class)
public interface LawServiceClient {
    // ...
}
```

**启用 Feign 降级**：

```yaml
# application.yml
spring:
  cloud:
    openfeign:
      circuitbreaker:
        enabled: true
```

### 16.6 服务间调用示例

#### 示例 1：用户服务调用通用服务发送邮件

```java
// 通用服务提供邮件发送接口
@RestController
public class EmailFeignController {
    
    @PostMapping("/feign/email/send")
    public Result<Boolean> sendEmail(@RequestParam String to, 
                                     @RequestParam String subject, 
                                     @RequestParam String content) {
        // 发送邮件逻辑
        return Result.success(true);
    }
}

// 用户服务调用
@FeignClient(name = "law-common-service")
public interface EmailServiceClient {
    
    @PostMapping("/feign/email/send")
    Result<Boolean> sendEmail(@RequestParam("to") String to,
                              @RequestParam("subject") String subject,
                              @RequestParam("content") String content);
}
```

#### 示例 2：AI 服务调用用户服务获取用户信息

```java
// 用户服务提供用户信息接口
@RestController
public class UserFeignController {
    
    @GetMapping("/feign/user/info")
    public Result<Object> getUserInfo(@RequestParam Long userId) {
        // 获取用户信息逻辑
        return Result.success(userInfo);
    }
}

// AI 服务调用
@FeignClient(name = "law-user-service")
public interface UserServiceClient {
    
    @GetMapping("/feign/user/info")
    Result<Object> getUserInfo(@RequestParam("userId") Long userId);
}
```

### 16.7 服务间调用流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   前端       │────▶│   网关       │────▶│  用户服务    │
│  (浏览器)    │     │ (80端口)     │     │  (8081)     │
└─────────────┘     └─────────────┘     └─────────────┘
                           │                    │
                           │                    │ Feign 调用
                           ▼                    ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   AI 服务    │────▶│  法典服务    │
                    │  (8083)     │     │  (8082)     │
                    └─────────────┘     └─────────────┘
                           │
                           │ Feign 调用
                           ▼
                    ┌─────────────┐
                    │  通用服务    │
                    │  (8084)     │
                    └─────────────┘
```

### 16.8 服务间调用注意事项

1. **服务名称一致性**
  - `@FeignClient(name = "xxx")` 中的 name 必须与被调用方的 `spring.application.name` 完全一致

2. **接口路径一致性**
  - Feign 客户端定义的路径必须与被调用方 Controller 的路径完全一致

3. **参数名称一致性**
  - 使用 `@RequestParam` 时，参数名必须与被调用方一致
  - 或者使用 `@RequestParam("name")` 显式指定

4. **避免循环依赖**
  - 服务 A 调用服务 B，服务 B 不能再调用服务 A
  - 如果需要双向调用，考虑引入消息队列

5. **超时配置**
  - 根据业务场景合理配置超时时间
  - AI 服务调用可能需要较长超时时间

6. **降级处理**
  - 必须实现降级逻辑，避免服务不可用时级联失败

---

## 十七、完整迁移检查清单

### 17.1 代码迁移检查

- [ ] Result 类已提取到 law-common-core
- [ ] 异常类已提取到 law-common-core
- [ ] 实体类已提取到对应模块
- [ ] JWT 工具类已提取到 law-common-security
- [ ] OSS 工具类已提取到 law-common-oss
- [ ] Redis 工具类已提取到 law-common-redis
- [ ] 用户相关代码已迁移到 law-user-service
- [ ] 法典相关代码已迁移到 law-law-service
- [ ] AI 相关代码已迁移到 law-ai-service
- [ ] 通用功能代码已迁移到 law-common-service
- [ ] 所有包名已修改为新包名
- [ ] 所有 Mapper XML 的 namespace 已更新

### 17.2 配置迁移检查

- [ ] 父 POM 已创建并配置依赖管理
- [ ] 各模块 POM 已创建并配置依赖
- [ ] bootstrap.yml 已配置 Nacos 连接
- [ ] application.yml 已配置本地参数
- [ ] Nacos 配置中心已创建所有配置文件
- [ ] 共享配置 common.yml 已创建

### 17.3 数据库检查

- [ ] 数据库连接配置正确
- [ ] 各服务能正常访问数据库
- [ ] Mapper XML 中的 SQL 语句正确

### 17.4 服务注册检查

- [ ] Nacos 服务已启动
- [ ] 各服务能注册到 Nacos
- [ ] Nacos 控制台能看到所有服务

### 17.5 服务调用检查

- [ ] Feign 客户端接口已创建
- [ ] Feign 降级逻辑已实现
- [ ] 服务间调用测试通过

### 17.6 功能测试检查

- [ ] 用户注册登录功能正常
- [ ] 法典浏览功能正常
- [ ] AI 咨询功能正常
- [ ] 文件上传功能正常
- [ ] 轮播图显示正常

---

## 十八、更新日志

### v1.1 (2026-05-20)

**主要变更**：
- 升级 Nacos 从 2.3.x 到 3.2.1
- 升级 Spring Cloud Alibaba 从 2023.0.1.0 到 2023.0.1.2
- 添加 Nacos 3.x gRPC 端口配置（9848, 9849）

**新增内容**：
- 添加 Nacos 3.2.1 重要说明章节
- 添加 Nacos 3.2.1 特别注意事项章节
- 添加 Java 17+ 版本要求说明
- 添加 Docker 部署中 gRPC 端口暴露配置
- 添加 Nacos 配置创建详细步骤

**兼容性说明**：
- Nacos 3.x 需要 Java 17+ 运行环境
- Spring Cloud Alibaba 2023.0.1.2 与 Nacos 3.2.1 完全兼容
- 客户端配置方式保持不变

### v1.0 (初始版本)

- 初始微服务改造方案
- 基于 Nacos 2.3.x
