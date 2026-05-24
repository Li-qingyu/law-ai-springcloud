package org.lawcommonsecurity.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.Map;

@Component
public class JwtUtil {

    private SecretKey getSecretKey(String secretKey) {
        return io.jsonwebtoken.security.Keys.hmacShaKeyFor(secretKey.getBytes(StandardCharsets.UTF_8));
    }

    /**
     * 生成jwt
     *
     * @param secretKey jwt秘钥
     * @param ttlMillis jwt过期时间(毫秒)
     * @param claims    设置的信息
     * @return
     */
    public String createJWT(String secretKey, long ttlMillis, Map<String, Object> claims) {
        long expMillis = System.currentTimeMillis() + ttlMillis;
        Date exp = new Date(expMillis);

        return Jwts.builder()
                .claims(claims)
                .signWith(getSecretKey(secretKey))
                .expiration(exp)
                .compact();
    }

    /**
     * Token解密
     *
     * @param secretKey jwt秘钥
     * @param token     加密后的token
     * @return
     */
    public Claims parseJWT(String secretKey, String token) {
        return Jwts.parser()
                .verifyWith(getSecretKey(secretKey))
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }
}
