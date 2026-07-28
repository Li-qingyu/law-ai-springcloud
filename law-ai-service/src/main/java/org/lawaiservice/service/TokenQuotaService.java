package org.lawaiservice.service;

import java.util.Map;

public interface TokenQuotaService {

    boolean checkQuota(Integer userId);

    void recordUsage(Integer userId, String sessionId, String provider, String modelName,
                     int inputTokens, int outputTokens, int totalTokens, String requestType);

    void recordUsage(Integer userId, String sessionId, Map<String, Object> tokenUsage);

    void resetUser(Integer userId);

    void resetDaily();

    void resetMonthly();
}
