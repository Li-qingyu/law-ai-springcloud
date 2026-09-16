package org.lawcommonsecurity.annotation;

import org.lawcommonsecurity.constant.UserRole;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 角色授权注解 —— 打在 Service 方法（推荐，MVC 与后续 MCP 共同咽喉）或 Controller 方法上。
 * 由 {@link org.lawcommonsecurity.aspect.RequireRoleAspect} 统一执行：
 * 仅允许 {@code value} 中包含的角色调用；内部调用（BaseContext.isInternal()）自动跳过。
 * 示例：{@code @RequireRole(UserRole.SUPER_ADMIN)} 仅超管；{@code @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})} 管理员及以上。
 */
@Target({ElementType.METHOD, ElementType.TYPE})
@Retention(RetentionPolicy.RUNTIME)
public @interface RequireRole {

    UserRole[] value();
}
