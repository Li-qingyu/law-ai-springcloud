package org.lawcommonsecurity.constant;

/**
 * Token 相关常量
 */
public class TokenConstant {

    /**
     * Redis 中用户 Token 会话缓存 Key 前缀：user:token:{userId}
     */
    public static final String USER_TOKEN_REDIS_KEY_PREFIX = "user:token:";

    /**
     * 默认缓存时长（秒），与 JWT 过期时间对齐
     */
    public static final long DEFAULT_CACHE_TTL_SECONDS = 7 * 24 * 3600L;
}
