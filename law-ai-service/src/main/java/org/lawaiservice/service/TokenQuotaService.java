package org.lawaiservice.service;

import java.util.Map;

import org.lawcommoncore.entity.UserTokenQuota;

public interface TokenQuotaService {

    UserTokenQuota getQuota(Integer userId);

    boolean checkQuota(Integer userId);

    void recordUsage(Integer userId, String sessionId, String provider, String modelName,
                     int inputTokens, int outputTokens, int totalTokens, String requestType);

    void recordUsage(Integer userId, String sessionId, Map<String, Object> tokenUsage);

    void resetUser(Integer userId);

    void resetDaily();

    void resetMonthly();
}
