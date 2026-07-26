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
                Integer guestId = Integer.valueOf(claims.get("guestId").toString());
                log.info("JWT校验通过，游客id: {}, 路径: {}", guestId, path);
                mutatedRequest = request.mutate()
                        .header("X-Guest-Id", String.valueOf(guestId))
                        .header("X-User-Type", "guest")
                        .build();
            } else {
                Integer userId = Integer.valueOf(claims.get("userId").toString());
                log.info("JWT校验通过，用户id: {}, 路径: {}", userId, path);
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
