package org.lawgateway.filter;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.context.properties.ConfigurationProperties;
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

import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Component
@ConfigurationProperties(prefix = "gateway")
public class AuthGlobalFilter implements GlobalFilter, Ordered {

    @Value("${law.jwt.admin-secret-key:lawai}")
    private String secretKey;

    @Value("${law.jwt.admin-token-name:token}")
    private String tokenName;

    private List<String> whitelist = new ArrayList<>();

    public void setWhitelist(List<String> whitelist) {
        this.whitelist = whitelist;
    }

    public List<String> getWhitelist() {
        return whitelist;
    }

    private static final AntPathMatcher PATH_MATCHER = new AntPathMatcher();

    private static final List<String> PUBLIC_PATHS = List.of(
            "/guest/init"
    );

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();
        String path = request.getURI().getPath();

        // 白名单放行（Nacos配置 + 硬编码公共路径）
        if (isWhitelist(path) || PUBLIC_PATHS.stream().anyMatch(p -> PATH_MATCHER.match(p, path))) {
            log.info(path + "是白名单");
            return chain.filter(exchange);
        }

        // 获取token（优先从Header获取，SSE等不支持Header的场景从Query参数获取）
        String token = request.getHeaders().getFirst(tokenName);
        if (token == null || token.isEmpty()) {
            token = request.getQueryParams().getFirst(tokenName);
        }
        if (token == null || token.isEmpty()) {
            log.warn("请求缺少token: {}", path);
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }

        // 解析token
        try {
            Claims claims = Jwts.parser()
                    .verifyWith(Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8)))
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();

            String type = claims.get("type", String.class);
            ServerHttpRequest mutatedRequest;

            if ("guest".equals(type)) {
                // 游客禁止访问管理接口
                if (isAdminPath(path)) {
                    log.warn("游客无权访问管理接口: path={}", path);
                    ServerHttpResponse response = exchange.getResponse();
                    response.setStatusCode(HttpStatus.FORBIDDEN);
                    return response.setComplete();
                }
                Integer guestId = Integer.valueOf(claims.get("guestId").toString());
                log.info("JWT校验通过，游客id: {}, 路径: {}", guestId, path);
                mutatedRequest = request.mutate()
                        .header("X-Guest-Id", String.valueOf(guestId))
                        .header("X-User-Type", "guest")
                        .build();
            } else {
                Integer userId = Integer.valueOf(claims.get("userId").toString());
                Integer role = claims.get("role", Integer.class);

                // 网关只做粗筛：普通用户(role=0/null)仅放行用户端只读浏览 + 本人资料；
                // 管理员(role=1/2)直通，具体角色权限由各服务层 @RequireRole 切面判定。
                if ((role == null || role == 0) && isAdminPath(path)
                        && !isPublicReadOnlyAdminPath(path, request.getMethod().name())) {
                    log.warn("权限不足: userId={}, role={}, path={}", userId, role, path);
                    ServerHttpResponse response = exchange.getResponse();
                    response.setStatusCode(HttpStatus.FORBIDDEN);
                    return response.setComplete();
                }

                log.info("JWT校验通过，用户id: {}, 角色: {}, 路径: {}", userId, role, path);
                mutatedRequest = request.mutate()
                        .header("X-User-Id", String.valueOf(userId))
                        .header("X-User-Type", "user")
                        .build();
            }

            return chain.filter(exchange.mutate().request(mutatedRequest).build());
        } catch (Exception e) {
            log.error("JWT校验失败: {}", e.getMessage());
            ServerHttpResponse response = exchange.getResponse();
            response.setStatusCode(HttpStatus.UNAUTHORIZED);
            return response.setComplete();
        }
    }

    // 所有 /admin/** 均视为管理路径：游客一律拒绝；
    // 普通用户(role=0)仅放行 isPublicReadOnlyAdminPath 中声明的只读浏览路径；
    // 管理员(role=1/2)直通，具体角色权限由各服务层 @RequireRole 切面判定。
    private static final String ADMIN_PATH_PATTERN = "/admin/**";

    // 普通用户可访问的管理路径白名单（只读浏览 + 本人资料），
    // 与用户端页面实际调用的接口保持一致（案例/法典浏览复用这些只读接口）。
    private static final List<String> PUBLIC_READ_ONLY_ADMIN_PATHS = List.of(
            "GET /admin/case/**",
            "GET /admin/law-articles/**",
            "GET /admin/law-books/**",
            "GET /admin/types/**",
            "GET /admin/users/*"
    );

    private boolean isAdminPath(String path) {
        return PATH_MATCHER.match(ADMIN_PATH_PATTERN, path);
    }

    /**
     * 判断普通用户的"管理路径只读白名单"命中情况：
     * 白名单条目格式为 "METHOD pattern"，要求 HTTP 方法与路径同时匹配；
     * 带路径参数的写操作（如 POST /admin/case）因方法不匹配而被拒绝。
     */
    private boolean isPublicReadOnlyAdminPath(String path, String method) {
        return PUBLIC_READ_ONLY_ADMIN_PATHS.stream().anyMatch(entry -> {
            int spaceIdx = entry.indexOf(' ');
            String allowedMethod = entry.substring(0, spaceIdx);
            String pattern = entry.substring(spaceIdx + 1);
            return allowedMethod.equalsIgnoreCase(method) && PATH_MATCHER.match(pattern, path);
        });
    }

    private boolean isWhitelist(String path) {
        if (whitelist == null || whitelist.isEmpty()) {
            return false;
        }
        return whitelist.stream().anyMatch(pattern -> PATH_MATCHER.match(pattern, path));
    }

    @Override
    public int getOrder() {
        return -100;
    }
}
