package org.lawaiservice.service;

import org.lawcommoncore.entity.AiConfig;

import java.util.List;

public interface AiConfigService {

    List<AiConfig> listAll();

    AiConfig getById(Integer id);

    AiConfig getDefaultConfig();

    AiConfig getConfig(String provider);

    int add(AiConfig aiConfig);

    int update(AiConfig aiConfig);

    int delete(Integer id);

    void setDefault(Integer id);

    void syncConfigToRedis();

    void syncConfigToRedis(String provider);
}
