package org.lawaiservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.service.AiConfigService;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.entity.AiConfig;
import org.lawcommoncore.result.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/admin/ai-config")
@Slf4j
public class AdminAiConfigController {

    @Autowired
    private AiConfigService aiConfigService;

    @GetMapping("/list")
    public Result<List<AiConfig>> list() {
        log.info("[AdminAiConfig] 查询配置列表, userId={}", BaseContext.getCurrentId());
        return Result.success(aiConfigService.listAll());
    }

    @GetMapping("/{id}")
    public Result<AiConfig> getById(@PathVariable Integer id) {
        AiConfig config = aiConfigService.getById(id);
        if (config == null) {
            return Result.error("配置不存在");
        }
        // 脱敏：只展示前7位和后4位
        String key = config.getApiKey();
        if (key != null && key.length() > 8) {
            config.setApiKey(key.substring(0, 7) + "..." + key.substring(key.length() - 4));
        }
        return Result.success(config);
    }

    @PostMapping
    public Result<Object> add(@RequestBody AiConfig aiConfig) {
        // 参数校验
        if (aiConfig.getProvider() == null || aiConfig.getProvider().isEmpty()) {
            return Result.error("提供商不能为空");
        }
        if (aiConfig.getModelName() == null || aiConfig.getModelName().isEmpty()) {
            return Result.error("模型名称不能为空");
        }
        if (aiConfig.getApiKey() == null || aiConfig.getApiKey().isEmpty()) {
            return Result.error("API Key不能为空");
        }

        try {
            aiConfigService.add(aiConfig);
            log.info("[AdminAiConfig] 新增配置: provider={}, modelName={}", aiConfig.getProvider(), aiConfig.getModelName());
            return Result.success();
        } catch (RuntimeException e) {
            return Result.error(e.getMessage());
        }
    }

    @PutMapping("/{id}")
    public Result<Object> update(@PathVariable Integer id, @RequestBody AiConfig aiConfig) {
        aiConfig.setId(id);
        try {
            aiConfigService.update(aiConfig);
            log.info("[AdminAiConfig] 更新配置: id={}", id);
            return Result.success();
        } catch (RuntimeException e) {
            return Result.error(e.getMessage());
        }
    }

    @DeleteMapping("/{id}")
    public Result<Object> delete(@PathVariable Integer id) {
        try {
            aiConfigService.delete(id);
            log.info("[AdminAiConfig] 删除配置: id={}", id);
            return Result.success();
        } catch (RuntimeException e) {
            return Result.error(e.getMessage());
        }
    }

    @PutMapping("/{id}/default")
    public Result<Object> setDefault(@PathVariable Integer id) {
        try {
            aiConfigService.setDefault(id);
            log.info("[AdminAiConfig] 设为默认: id={}", id);
            return Result.success();
        } catch (RuntimeException e) {
            return Result.error(e.getMessage());
        }
    }
}
