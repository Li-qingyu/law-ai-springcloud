package org.lawcommonsecurity.constant;

/**
 * 用户角色枚举 —— 角色的唯一权威表示
 * 与 user.role 整数值一一对应：0=普通用户，1=超级管理员，2=普通管理员
 * 授权（@RequireRole / AuthorizationService）、MCP 工具注册表、Python 权限矩阵均以此口径对齐。
 */
public enum UserRole {

    /** 普通用户：只读浏览知识库 + 本人资料 */
    USER(0),
    /** 超级管理员：全部能力（Token管理、用户管理、AI配置、知识库、AI数据助手） */
    SUPER_ADMIN(1),
    /** 普通管理员：知识库完整维护 + AI数据助手（按角色限定操作） */
    ADMIN(2);

    private final int code;

    UserRole(int code) {
        this.code = code;
    }

    public int getCode() {
        return code;
    }

    /**
     * 由数据库/ThreadLocal 中的整数值解析角色，null 或未知值按 USER 处理
     */
    public static UserRole of(Integer code) {
        if (code == null) {
            return USER;
        }
        for (UserRole r : values()) {
            if (r.code == code) {
                return r;
            }
        }
        return USER;
    }
}
