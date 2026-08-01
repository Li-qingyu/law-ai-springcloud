package org.lawaiservice.service.Impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.mapper.AiConfigMapper;
import org.lawaiservice.service.AiConfigService;
import org.lawaiservice.utils.AesEncryptUtil;
import org.lawcommoncore.entity.AiConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

@Service
@Slf4j
public class AiConfigServiceImpl implements AiConfigService {

    private static final String REDIS_KEY_DEFAULT = "ai:config:default";
    private static final String REDIS_KEY_PROVIDERS = "ai:config:providers";
    private static final String REDIS_KEY_ALL_KEYS = "ai:config:all_keys";
    private static final long REDIS_TTL = 7 * 24 * 60 * 60;

    @Autowired
    private AiConfigMapper aiConfigMapper;

    @Autowired
    private AesEncryptUtil aesEncryptUtil;

    @Autowired
    private StringRedisTemplate stringRedisTemplate;

    @Autowired
    private ObjectMapper objectMapper;

    // ==================== 查询接口 ====================

    @Override
    public List<AiConfig> listAll() {
        List<AiConfig> list = aiConfigMapper.selectList();
        for (AiConfig config : list) {
            maskApiKey(config);
        }
        return list;
    }

    @Override
    public AiConfig getById(Integer id) {
        return aiConfigMapper.selectById(id);
    }

    @Override
    public AiConfig getDefaultConfig() {
        AiConfig config = aiConfigMapper.selectDefault();
        if (config != null) {
            config.setApiKey(tryDecrypt(config.getApiKey()));
        }
        return config;
    }

    @Override
    public AiConfig getConfig(String provider) {
        AiConfig config = aiConfigMapper.selectByProvider(provider);
        if (config != null) {
            config.setApiKey(tryDecrypt(config.getApiKey()));
        }
        return config;
    }

    // ==================== 写入接口 ====================

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int add(AiConfig aiConfig) {
        // 1. 重复校验
        int dup = aiConfigMapper.countByProviderModel(aiConfig.getProvider(), aiConfig.getModelName(), null);
        if (dup > 0) {
            throw new RuntimeException("已存在相同提供商和模型的配置: " + aiConfig.getProvider() + "/" + aiConfig.getModelName());
        }

        // 2. 如果设为默认，校验 status 不能为禁用
        if (aiConfig.getIsDefault() != null && aiConfig.getIsDefault() == 1) {
            if (aiConfig.getStatus() != null && aiConfig.getStatus() == 0) {
                throw new RuntimeException("禁用的配置不能设为默认");
            }
            aiConfigMapper.clearDefault();
        }

        // 3. 加密 API Key
        aiConfig.setApiKey(aesEncryptUtil.encrypt(aiConfig.getApiKey()));

        // 4. 插入
        int result = aiConfigMapper.insert(aiConfig);

        // 5. 同步 Redis
        syncConfigToRedis();
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int update(AiConfig aiConfig) {
        // 1. 校验配置是否存在
        AiConfig existing = aiConfigMapper.selectById(aiConfig.getId());
        if (existing == null) {
            throw new RuntimeException("配置不存在: id=" + aiConfig.getId());
        }

        // 2. 如果修改了 provider 或 model_name，校验重复
        String newProvider = aiConfig.getProvider() != null ? aiConfig.getProvider() : existing.getProvider();
        String newModelName = aiConfig.getModelName() != null ? aiConfig.getModelName() : existing.getModelName();
        int dup = aiConfigMapper.countByProviderModel(newProvider, newModelName, aiConfig.getId());
        if (dup > 0) {
            throw new RuntimeException("已存在相同提供商和模型的配置: " + newProvider + "/" + newModelName);
        }

        // 3. 如果设为默认，校验 status
        if (aiConfig.getIsDefault() != null && aiConfig.getIsDefault() == 1) {
            int targetStatus = aiConfig.getStatus() != null ? aiConfig.getStatus() : existing.getStatus();
            if (targetStatus == 0) {
                throw new RuntimeException("禁用的配置不能设为默认");
            }
            aiConfigMapper.clearDefault();
        }

        // 4. 加密 API Key（非 null 且非已加密格式时加密）
        if (aiConfig.getApiKey() != null && !isEncrypted(aiConfig.getApiKey())) {
            aiConfig.setApiKey(aesEncryptUtil.encrypt(aiConfig.getApiKey()));
        }

        // 5. 更新
        int result = aiConfigMapper.updateById(aiConfig);

        // 6. 同步 Redis
        syncConfigToRedis();
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int delete(Integer id) {
        // 1. 校验配置是否存在
        AiConfig target = aiConfigMapper.selectById(id);
        if (target == null) {
            throw new RuntimeException("配置不存在: id=" + id);
        }

        boolean wasDefault = target.getIsDefault() != null && target.getIsDefault() == 1;

        // 2. 执行删除
        int result = aiConfigMapper.deleteById(id);

        // 3. 如果删除的是默认配置，从剩余启用配置中选一个作为新默认
        if (wasDefault) {
            AiConfig newDefault = null;
            List<AiConfig> remaining = aiConfigMapper.selectList();
            for (AiConfig config : remaining) {
                if (config.getStatus() != null && config.getStatus() == 1) {
                    newDefault = config;
                    break;
                }
            }
            if (newDefault != null) {
                aiConfigMapper.setDefault(newDefault.getId());
                log.info("[AdminAiConfig] 默认配置已删除，自动切换新默认: id={}, provider={}",
                        newDefault.getId(), newDefault.getProvider());
            } else {
                log.warn("[AdminAiConfig] 默认配置已删除，无可用的启用配置");
            }
        }

        // 4. 同步 Redis
        syncConfigToRedis();
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void setDefault(Integer id) {
        // 1. 校验目标配置存在且启用
        AiConfig target = aiConfigMapper.selectById(id);
        if (target == null) {
            throw new RuntimeException("配置不存在: id=" + id);
        }
        if (target.getStatus() != null && target.getStatus() == 0) {
            throw new RuntimeException("禁用的配置不能设为默认");
        }

        // 2. 清除旧默认，设置新默认
        aiConfigMapper.clearDefault();
        aiConfigMapper.setDefault(id);

        // 3. 同步 Redis
        syncConfigToRedis();
    }

    // ==================== Redis 同步 ====================

    @Override
    public void syncConfigToRedis() {
        try {
            // 1. 同步默认配置
            AiConfig defaultConfig = aiConfigMapper.selectDefault();
            if (defaultConfig != null) {
                defaultConfig.setApiKey(tryDecrypt(defaultConfig.getApiKey()));
                stringRedisTemplate.opsForValue().set(
                        REDIS_KEY_DEFAULT,
                        objectMapper.writeValueAsString(defaultConfig),
                        REDIS_TTL, TimeUnit.SECONDS);
            } else {
                stringRedisTemplate.delete(REDIS_KEY_DEFAULT);
            }

            // 2. 同步所有启用配置，收集当前活跃的 key
            List<AiConfig> allConfigs = aiConfigMapper.selectList();
            Set<String> activeKeys = new HashSet<>();

            for (AiConfig config : allConfigs) {
                String key = configKey(config.getProvider(), config.getModelName());
                if (config.getStatus() != null && config.getStatus() == 1) {
                    config.setApiKey(tryDecrypt(config.getApiKey()));
                    stringRedisTemplate.opsForValue().set(
                            key,
                            objectMapper.writeValueAsString(config),
                            REDIS_TTL, TimeUnit.SECONDS);
                    activeKeys.add(key);
                }
            }

            // 3. 清理已禁用/已删除的配置 key
            Set<String> trackedKeys = stringRedisTemplate.opsForSet().members(REDIS_KEY_ALL_KEYS);
            if (trackedKeys != null) {
                for (String oldKey : trackedKeys) {
                    if (!activeKeys.contains(oldKey)) {
                        stringRedisTemplate.delete(oldKey);
                    }
                }
            }
            // 更新跟踪集合
            stringRedisTemplate.delete(REDIS_KEY_ALL_KEYS);
            if (!activeKeys.isEmpty()) {
                stringRedisTemplate.opsForSet().add(REDIS_KEY_ALL_KEYS, activeKeys.toArray(new String[0]));
                stringRedisTemplate.expire(REDIS_KEY_ALL_KEYS, REDIS_TTL, TimeUnit.SECONDS);
            }

            // 4. 同步 provider 列表（只保留有启用配置的 provider）
            Set<String> activeProviders = allConfigs.stream()
                    .filter(c -> c.getStatus() != null && c.getStatus() == 1 && c.getProvider() != null)
                    .map(AiConfig::getProvider)
                    .collect(Collectors.toSet());
            stringRedisTemplate.delete(REDIS_KEY_PROVIDERS);
            if (!activeProviders.isEmpty()) {
                stringRedisTemplate.opsForSet().add(REDIS_KEY_PROVIDERS, activeProviders.toArray(new String[0]));
                stringRedisTemplate.expire(REDIS_KEY_PROVIDERS, REDIS_TTL, TimeUnit.SECONDS);
            }

            log.info("[AiConfig] syncConfigToRedis 完成, 活跃配置数={}, provider数={}",
                    activeKeys.size(), activeProviders.size());
        } catch (Exception e) {
            log.error("[AiConfig] syncConfigToRedis 失败", e);
        }
    }

    @Override
    public void syncConfigToRedis(String provider) {
        // 同 provider 可能有多条配置（不同 model_name），直接全量同步更可靠
        syncConfigToRedis();
    }

    // ==================== 内部方法 ====================

    private static String configKey(String provider, String modelName) {
        return "ai:config:" + provider + ":" + modelName;
    }

    /**
     * 尝试解密，失败则原样返回（兼容数据库中未加密的明文 key）
     */
    private String tryDecrypt(String apiKey) {
        if (apiKey == null) return null;
        try {
            return aesEncryptUtil.decrypt(apiKey);
        } catch (Exception e) {
            log.warn("[AiConfig] API Key 解密失败，按明文处理: {}", e.getMessage());
            return apiKey;
        }
    }

    /**
     * 判断 API Key 是否已经过 AES 加密
     * 加密后的格式为 Base64 编码（不含空格，长度较长），明文通常含可见 ASCII 字符
     */
    private boolean isEncrypted(String apiKey) {
        if (apiKey == null || apiKey.isEmpty()) return false;
        // 加密后的 key 是 Base64 格式，长度通常 > 40，且不含中文/空格
        // 简单判断：如果是合法 Base64 且长度合理，视为已加密
        return apiKey.length() > 40 && apiKey.matches("^[A-Za-z0-9+/=]+$");
    }

    private void maskApiKey(AiConfig config) {
        String key = config.getApiKey();
        if (key != null && key.length() > 8) {
            config.setApiKey(key.substring(0, 7) + "..." + key.substring(key.length() - 4));
        }
    }
}
