package org.lawaiservice.mcp.registry;

import lombok.extern.slf4j.Slf4j;
import org.lawcommonsecurity.constant.UserRole;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationContext;
import org.springframework.context.event.EventListener;
import org.springframework.core.annotation.AnnotatedElementUtils;
import org.springframework.stereotype.Component;

import java.lang.reflect.Method;
import java.util.Map;
import java.util.Set;

/**
 * MCP 工具注册表 —— 唯一真相源
 * <p>启动期 fail-fast:所有已注册的 MCP 工具(@McpTool)必须在此登记权限条目,
 * 缺失即启动失败,防止"新增工具忘配权限"被静默漏网。</p>
 * <p>二期权限入库后,本类数据源切换为读 sys_role_permission 表,声明形态不变。</p>
 */
@Slf4j
@Component
public class McpToolRegistry {

    /**
     * 工具 → 允许角色
     * 权限矩阵与 Python PERMISSION_MATRIX.data_management 对齐(实施设计文档 §3.4/§7):
     * data_management 全部操作 admin 可用,super_admin 继承全部。
     */
    private static final Map<String, Set<UserRole>> TOOL_ROLES = Map.ofEntries(
            // ── law_article ──
            Map.entry("law_article_query", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_create", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_update", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_delete", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_import", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_sync", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_sync_status", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_article_count", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            // ── law_case ──
            Map.entry("law_case_query", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_create", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_update", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_delete", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_sync", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_sync_status", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_case_count", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            // ── law_book ──
            Map.entry("law_book_query", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_book_query_all", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_book_create", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_book_update", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_book_delete", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            // ── law_type ──
            Map.entry("law_type_query", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_type_query_all", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_type_create", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_type_update", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_type_delete", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN)),
            Map.entry("law_type_count", Set.of(UserRole.ADMIN, UserRole.SUPER_ADMIN))
    );

    /** 是否允许角色调用指定工具 */
    public boolean isAllowed(String toolName, UserRole role) {
        Set<UserRole> roles = TOOL_ROLES.get(toolName);
        if (roles == null) {
            // 白名单语义:未登记的工具一律拒绝(不问角色)
            return false;
        }
        return roles.contains(role);
    }

    /**
     * fail-fast:扫描全部 bean 方法上的 @McpTool,凡未在 TOOL_ROLES 登记者启动失败
     */
    @Autowired
    private ApplicationContext applicationContext;

    @EventListener(ApplicationReadyEvent.class)
    public void validateToolRegistry() {
        int registered = 0;
        for (Object bean : applicationContext.getBeansWithAnnotation(Component.class).values()) {
            for (Method method : bean.getClass().getDeclaredMethods()) {
                var ann = AnnotatedElementUtils.findMergedAnnotation(method,
                        org.springaicommunity.mcp.annotation.McpTool.class);
                if (ann != null) {
                    registered++;
                    if (!TOOL_ROLES.containsKey(ann.name())) {
                        throw new IllegalStateException(
                                "MCP工具未在 McpToolRegistry 登记权限条目,拒绝启动: " + ann.name()
                                + " (bean=" + bean.getClass().getSimpleName() + ")");
                    }
                }
            }
        }
        log.info("MCP工具注册表校验通过: {} 个@McpTool 全部已登记权限, TOOR_ROLES 共 {} 条", registered, TOOL_ROLES.size());
    }
}
