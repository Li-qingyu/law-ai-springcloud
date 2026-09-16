package org.lawcommonsecurity.service;

import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.exception.AuthorizationException;
import org.lawcommonsecurity.constant.UserRole;
import org.springframework.stereotype.Component;

/**
 * 角色授权服务 —— 唯一授权决策点。
 * MVC 控制器、以及后续 MCP 工具（直连 Service）都复用同一决策，保证多入口权限一致。
 */
@Component
public class AuthorizationService {

    /**
     * 校验当前请求角色是否在允许集合内，不满足抛 {@link AuthorizationException}。
     */
    public void requireRole(UserRole... allowed) {
        Integer roleCode = BaseContext.getCurrentRole();
        UserRole current = UserRole.of(roleCode);
        for (UserRole role : allowed) {
            if (role == current) {
                return;
            }
        }
        throw new AuthorizationException("权限不足");
    }
}
