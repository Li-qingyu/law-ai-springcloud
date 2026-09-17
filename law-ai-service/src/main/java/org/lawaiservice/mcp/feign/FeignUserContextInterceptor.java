package org.lawaiservice.mcp.feign;

import feign.RequestInterceptor;
import feign.RequestTemplate;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.context.BaseContext;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

/**
 * MCP 链路 Feign 凭证转发拦截器(仅 law-ai-service 的 Feign 出口生效于 MCP 用户链路)
 * <p>透传原始用户 token:从当前 HTTP 请求(RequestContextHolder)取「token」头,
 * 原样放到 Feign 请求上——下游 JwtTokenInterceptor 走正常用户分支
 * (JWT + Redis 会话校验 → BaseContext → @RequireRole 生效),下游零改造。</p>
 * <p>与 FeignInternalInterceptor 的关系:MCP 用户链路剥离 X-Internal-Call(绝不是内部调用);
 * 无用户语境的系统级调用(定时任务等)不受影响,仍由其加 internal 头走互信通道。</p>
 */
@Slf4j
@Component
@Order(1)   // 先于 FeignInternalInterceptor,确保先剥头,系统调用再由其补头
public class FeignUserContextInterceptor implements RequestInterceptor {

    @Override
    public void apply(RequestTemplate template) {
        // 仅在「用户语境 + 非 internal」时透传(MCP 用户链路特征)
        Integer userId = BaseContext.getCurrentId();
        boolean internal = BaseContext.isInternal();
        if (userId != null || !internal) {
            ServletRequestAttributes attrs =
                    (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
            if (attrs != null) {
                HttpServletRequest origin = attrs.getRequest();
                String token = origin.getHeader("token");
                if (token != null && !token.isBlank()) {
                    template.header("token", token);
                    template.removeHeader("X-Internal-Call");
                    log.debug("MCP链路 Feign 透传用户 token -> {}", template.url());
                }
            }
        }
    }
}
