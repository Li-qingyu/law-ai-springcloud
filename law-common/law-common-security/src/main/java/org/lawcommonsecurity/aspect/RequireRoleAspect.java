package org.lawcommonsecurity.aspect;

import lombok.extern.slf4j.Slf4j;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.lawcommoncore.context.BaseContext;
import org.lawcommonsecurity.annotation.RequireRole;
import org.lawcommonsecurity.service.AuthorizationService;
import org.springframework.core.Ordered;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * 角色授权切面 —— 执行 {@link RequireRole} 注解。
 * 排在 @Transactional 之前（先授权、后开事务）；内部调用（BaseContext.isInternal()）跳过。
 * 授权决策统一委托 {@link AuthorizationService}。
 */
@Slf4j
@Aspect
@Order(1)
@Component
public class RequireRoleAspect {

    private final AuthorizationService authorizationService;

    public RequireRoleAspect(AuthorizationService authorizationService) {
        this.authorizationService = authorizationService;
    }

    /**
     * 方法级注解：@RequireRole 直接打在方法上，方法优先于类
     */
    @Around("@annotation(methodRequireRole)")
    public Object checkMethod(ProceedingJoinPoint pjp, RequireRole methodRequireRole) throws Throwable {
        if (BaseContext.isInternal()) {
            log.debug("内部调用跳过角色校验: {}", pjp.getSignature().toShortString());
            return pjp.proceed();
        }
        authorizationService.requireRole(methodRequireRole.value());
        return pjp.proceed();
    }

    /**
     * 类级注解：@RequireRole 打在类上（方法未标注解时生效，如 AdminTokenQuotaController）
     */
    @Around("@within(classRequireRole) && !@annotation(org.lawcommonsecurity.annotation.RequireRole)")
    public Object checkClass(ProceedingJoinPoint pjp, RequireRole classRequireRole) throws Throwable {
        if (BaseContext.isInternal()) {
            log.debug("内部调用跳过角色校验: {}", pjp.getSignature().toShortString());
            return pjp.proceed();
        }
        authorizationService.requireRole(classRequireRole.value());
        return pjp.proceed();
    }
}
