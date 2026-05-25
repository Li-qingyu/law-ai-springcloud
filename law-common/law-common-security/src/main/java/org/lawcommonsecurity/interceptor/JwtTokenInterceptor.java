package org.lawcommonsecurity.interceptor;

import io.jsonwebtoken.Claims;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.context.BaseContext;
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
    /**
     * 检验令牌
     */
    @Override
    public boolean preHandle(HttpServletRequest  request, HttpServletResponse response, Object handler) throws  Exception {
        // 内部服务调用，直接放行
        String internalCall = request.getHeader("X-Internal-Call");
        if ("true".equals(internalCall)) {
            return true;
        }

        String token = request.getHeader(jwtProperties.getAdminTokenName());
        try{
            log.info("检验令牌");
            Claims claims= jwtUtil.parseJWT(jwtProperties.getAdminSecretKey(), token);
            Integer userId= Integer.valueOf(claims.get("userId").toString());
            log.info("用户id:{}", userId);
            BaseContext.setCurrentId(userId);
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
        BaseContext.removeCurrentId();
        log.debug("已清理ThreadLocal中的用户ID");
    }

}
