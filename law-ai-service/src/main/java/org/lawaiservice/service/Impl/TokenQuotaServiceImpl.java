package org.lawaiservice.service.Impl;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.mapper.TokenUsageLogMapper;
import org.springframework.scheduling.annotation.Async;
import org.lawaiservice.mapper.UserTokenQuotaMapper;
import org.lawaiservice.service.TokenQuotaService;
import org.lawcommoncore.entity.TokenUsageLog;
import org.lawcommoncore.entity.UserTokenQuota;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;
import java.time.LocalDate;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Map;

@Service
@Slf4j
public class TokenQuotaServiceImpl implements TokenQuotaService {

    @Autowired
    private UserTokenQuotaMapper userTokenQuotaMapper;

    @Autowired
    private TokenUsageLogMapper tokenUsageLogMapper;

    private final DateTimeFormatter monthFormatter = DateTimeFormatter.ofPattern("yyyy-MM");

    @Override
    public boolean checkQuota(Integer userId) {
        UserTokenQuota quota = userTokenQuotaMapper.selectByUserId(userId);

        // Plan B: 懒初始化 — 首次咨询时自动创建配额行
        if (quota == null) {
            userTokenQuotaMapper.initQuota(userId);
            quota = userTokenQuotaMapper.selectByUserId(userId);
            log.info("[TokenQuota] 懒初始化用户配额: userId={}", userId);
        }

        resetIfNeeded(quota);

        // 检查当前已用量是否已达上限（而非预测性检查）
        if (quota.getDailyLimit() > 0 && quota.getDailyUsed() >= quota.getDailyLimit()) {
            log.warn("[TokenQuota] 已达每日限额: userId={}, used={}, limit={}",
                    userId, quota.getDailyUsed(), quota.getDailyLimit());
            return false;
        }
        if (quota.getMonthlyLimit() > 0 && quota.getMonthlyUsed() >= quota.getMonthlyLimit()) {
            log.warn("[TokenQuota] 已达每月限额: userId={}, used={}, limit={}",
                    userId, quota.getMonthlyUsed(), quota.getMonthlyLimit());
            return false;
        }
        return true;
    }

    @Override
    public void recordUsage(Integer userId, String sessionId, String provider, String modelName,
                            int inputTokens, int outputTokens, int totalTokens, String requestType) {
        // 1. 先插入使用日志（即使后续配额更新失败，日志也不丢）
        try {
            TokenUsageLog logRecord = TokenUsageLog.builder()
                    .userId(userId)
                    .sessionId(sessionId)
                    .provider(provider)
                    .modelName(modelName)
                    .inputTokens(inputTokens)
                    .outputTokens(outputTokens)
                    .totalTokens(totalTokens)
                    .requestType(requestType)
                    .build();
            tokenUsageLogMapper.insert(logRecord);
        } catch (Exception e) {
            log.error("[TokenQuota] 插入token使用日志失败! userId={}, totalTokens={}", userId, totalTokens, e);
        }

        // 2. 更新用户配额统计
        try {
            int affected = userTokenQuotaMapper.updateUsage(userId, inputTokens, outputTokens, totalTokens);
            if (affected == 0) {
                log.warn("[TokenQuota] 更新配额失败，可能用户不存在: userId={}", userId);
            } else {
                log.info("[TokenQuota] 记录Token使用: userId={}, totalTokens={}, provider={}",
                        userId, totalTokens, provider);
            }
        } catch (Exception e) {
            log.error("[TokenQuota] 更新配额统计失败! userId={}, totalTokens={}", userId, totalTokens, e);
        }
    }

    @Override
    @Async
    public void recordUsage(Integer userId, String sessionId, Map<String, Object> tokenUsage) {
        if (tokenUsage == null) return;

        try {
            int inputTokens = toInt(tokenUsage.get("input_tokens"));
            int outputTokens = toInt(tokenUsage.get("output_tokens"));
            int totalTokens = toInt(tokenUsage.get("total_tokens"));
            String provider = toString(tokenUsage.get("provider"));
            String modelName = toString(tokenUsage.get("model_name"));

            recordUsage(userId, sessionId, provider, modelName, inputTokens, outputTokens, totalTokens, "consult");
        } catch (Exception e) {
            // 异步任务异常不会传播到调用方，必须兜底记录
            log.error("[TokenQuota] 异步记录token使用量失败! userId={}, sessionId={}, tokenUsage={}",
                    userId, sessionId, tokenUsage, e);
        }
    }

    @Override
    public void resetUser(Integer userId) {
        userTokenQuotaMapper.resetDaily(userId);
        String month = LocalDate.now().format(monthFormatter);
        userTokenQuotaMapper.resetMonthly(userId, month);
        log.info("[TokenQuota] 手动重置用户配额: userId={}", userId);
    }

    @Override
    @Scheduled(cron = "0 0 0 * * ?")
    public void resetDaily() {
        try {
            int affected = userTokenQuotaMapper.resetAllDaily();
            log.info("[TokenQuota] 定时任务: 已重置所有用户每日配额, 影响行数={}", affected);
        } catch (Exception e) {
            log.error("[TokenQuota] 定时任务: 重置每日配额失败", e);
        }
    }

    @Override
    @Scheduled(cron = "0 0 0 1 * ?")
    public void resetMonthly() {
        try {
            String month = LocalDate.now().format(monthFormatter);
            int affected = userTokenQuotaMapper.resetAllMonthly(month);
            log.info("[TokenQuota] 定时任务: 已重置所有用户每月配额, month={}, 影响行数={}", month, affected);
        } catch (Exception e) {
            log.error("[TokenQuota] 定时任务: 重置每月配额失败", e);
        }
    }

    private void resetIfNeeded(UserTokenQuota quota) {
        LocalDate today = LocalDate.now();

        if (quota.getLastResetDaily() == null
                || !quota.getLastResetDaily().toInstant().atZone(ZoneId.systemDefault()).toLocalDate().equals(today)) {
            userTokenQuotaMapper.resetDaily(quota.getUserId());
            quota.setDailyUsed(0L);
            quota.setLastResetDaily(java.sql.Date.valueOf(today));
        }

        String thisMonth = today.format(monthFormatter);
        if (quota.getLastResetMonthly() == null
                || !quota.getLastResetMonthly().equals(thisMonth)) {
            userTokenQuotaMapper.resetMonthly(quota.getUserId(), thisMonth);
            quota.setMonthlyUsed(0L);
            quota.setLastResetMonthly(thisMonth);
        }
    }

    private int toInt(Object value) {
        if (value instanceof Number) return ((Number) value).intValue();
        if (value instanceof String) return Integer.parseInt((String) value);
        return 0;
    }

    private String toString(Object value) {
        return value == null ? "" : value.toString();
    }
}
