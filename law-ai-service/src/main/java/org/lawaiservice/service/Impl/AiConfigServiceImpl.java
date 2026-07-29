package org.lawaiservice.service.Impl;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.mapper.AiConfigMapper;
import org.lawaiservice.service.AiConfigService;
import org.lawaiservice.utils.AesEncryptUtil;
import org.lawcommoncore.entity.AiConfig;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@Slf4j
public class AiConfigServiceImpl implements AiConfigService {

    @Autowired
    private AiConfigMapper aiConfigMapper;

    @Autowired
    private AesEncryptUtil aesEncryptUtil;

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
        AiConfig config = aiConfigMapper.selectById(id);
        if (config != null) {
            maskApiKey(config);
        }
        return config;
    }

    @Override
    public AiConfig getDefaultConfig() {
        AiConfig config = aiConfigMapper.selectDefault();
        if (config != null) {
            config.setApiKey(aesEncryptUtil.decrypt(config.getApiKey()));
        }
        return config;
    }

    @Override
    public AiConfig getConfig(String provider) {
        AiConfig config = aiConfigMapper.selectByProvider(provider);
        if (config != null) {
            config.setApiKey(aesEncryptUtil.decrypt(config.getApiKey()));
        }
        return config;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int add(AiConfig aiConfig) {
        aiConfig.setApiKey(aesEncryptUtil.encrypt(aiConfig.getApiKey()));
        if (aiConfig.getIsDefault() != null && aiConfig.getIsDefault() == 1) {
            aiConfigMapper.clearDefault();
        }
        return aiConfigMapper.insert(aiConfig);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public int update(AiConfig aiConfig) {
        if (aiConfig.getApiKey() != null && !aiConfig.getApiKey().startsWith("sk-")) {
            aiConfig.setApiKey(aesEncryptUtil.encrypt(aiConfig.getApiKey()));
        }
        if (aiConfig.getIsDefault() != null && aiConfig.getIsDefault() == 1) {
            aiConfigMapper.clearDefault();
        }
        return aiConfigMapper.updateById(aiConfig);
    }

    @Override
    public int delete(Integer id) {
        return aiConfigMapper.deleteById(id);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void setDefault(Integer id) {
        aiConfigMapper.clearDefault();
        aiConfigMapper.setDefault(id);
    }

    private void maskApiKey(AiConfig config) {
        String key = config.getApiKey();
        if (key != null && key.length() > 8) {
            config.setApiKey(key.substring(0, 7) + "..." + key.substring(key.length() - 4));
        }
    }
}
