package org.lawaiservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.service.AiConfigService;
import org.lawcommoncore.entity.AiConfig;
import org.lawcommoncore.result.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/internal/ai-config")
@Slf4j
public class InternalAiConfigController {

    @Autowired
    private AiConfigService aiConfigService;

    @GetMapping("/current")
    public Result<AiConfig> getCurrentConfig(@RequestParam(required = false) String provider) {
        AiConfig config;
        if (provider != null) {
            config = aiConfigService.getConfig(provider);
        } else {
            config = aiConfigService.getDefaultConfig();
        }
        if (config == null) {
            return Result.error("未找到可用的AI配置");
        }
        return Result.success(config);
    }
}
