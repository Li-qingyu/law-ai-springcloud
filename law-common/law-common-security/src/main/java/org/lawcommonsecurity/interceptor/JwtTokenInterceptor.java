package org.lawcommonsecurity.interceptor;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.context.BaseContext;
import org.lawcommonredis.utils.RedisUtil;
import org.lawcommonsecurity.constant.TokenConstant;
import org.lawcommonsecurity.properties.JwtProperties;
import org.lawcommonsecurity.utils.JwtUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

/**
 * jwt令牌检验
 */
@Slf4j
@Component
public class JwtTokenInterceptor implements HandlerInterceptor {
    @Autowired
    private JwtProperties jwtProperties;
    @Autowired
    private JwtUtil jwtUtil;
    @Autowired
    private RedisUtil redisUtil;
    /**
     * 检验令牌
     */
    @Override
    public boolean preHandle(HttpServletRequest  request, HttpServletResponse response, Object handler) throws  Exception {
        // 内部服务调用或内部接口，置内部标记后放行（授权切面据此跳过角色校验）
        String internalCall = request.getHeader("X-Internal-Call");
        if ("true".equals(internalCall)) {
            BaseContext.setInternal(true);
            return true;
        }
        if (request.getRequestURI().startsWith("/internal/")) {
            BaseContext.setInternal(true);
            return true;
        }

        String token = request.getHeader(jwtProperties.getAdminTokenName());

        try{
            log.info("检验令牌");
            Claims claims = jwtUtil.parseJWT(jwtProperties.getAdminSecretKey(), token);
            String type = claims.get("type", String.class);

            if ("guest".equals(type)) {
                Integer guestId = Integer.valueOf(claims.get("guestId").toString());
                log.info("游客id:{}", guestId);
                BaseContext.setCurrentGuestId(guestId);
                BaseContext.setUserType("guest");
            } else {
                Integer userId = Integer.valueOf(claims.get("userId").toString());
                log.info("用户id:{}", userId);
                // 校验 Redis 会话缓存中的 token 是否与当前 token 一致（不一致说明已被新登录顶替/登出/吊销）
                Object cachedToken = redisUtil.get(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + userId);
                if (cachedToken == null || !token.equals(cachedToken.toString())) {
                    log.warn("token无效或已失效，拒绝访问 userId:{}", userId);
                    response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                    return false;
                }
                BaseContext.setCurrentId(userId);
                BaseContext.setUserType("user");

                Object roleObj = claims.get("role");
                if (roleObj != null) {
                    Integer role = Integer.valueOf(roleObj.toString());
                    BaseContext.setCurrentRole(role);
                    log.info("用户角色:{}", role);
                }
            }

            return true;
        }catch (Exception e){
            response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
            return false;
        }

    }
    @Override
    public void afterCompletion(HttpServletRequest request,
                                HttpServletResponse response,
                                Object handler,
                                Exception ex) throws Exception {
        BaseContext.clear();
        log.debug("已清理ThreadLocal中的用户信息");
    }

}
