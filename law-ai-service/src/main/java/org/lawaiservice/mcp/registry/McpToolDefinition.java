package org.lawaiservice.mcp.registry;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.Set;

/**
 * MCP 工具注册表条目
 * <p>权限声明集中地(唯一真相源):每个 @McpTool 必须在此登记 requiredRole,
 * 否则启动期 fail-fast 校验直接失败——工具暴露面与权限声明永不脱节。</p>
 */
@Data
@AllArgsConstructor
public class McpToolDefinition {
    /** 工具名(snake_case,与 @McpTool.name 一致) */
    private String toolName;
    /** 允许调用的角色集合(对齐 org.lawcommonsecurity.constant.UserRole 的 role 值语义) */
    private Set<Integer> requiredRoles;
}
