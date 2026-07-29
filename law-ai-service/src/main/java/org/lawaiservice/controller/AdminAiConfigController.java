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
        return Result.success(aiConfigService.getById(id));
    }

    @PostMapping
    public Result<Object> add(@RequestBody AiConfig aiConfig) {
        aiConfigService.add(aiConfig);
        log.info("[AdminAiConfig] 新增配置: provider={}, modelName={}", aiConfig.getProvider(), aiConfig.getModelName());
        return Result.success();
    }

    @PutMapping("/{id}")
    public Result<Object> update(@PathVariable Integer id, @RequestBody AiConfig aiConfig) {
        aiConfig.setId(id);
        aiConfigService.update(aiConfig);
        log.info("[AdminAiConfig] 更新配置: id={}", id);
        return Result.success();
    }

    @DeleteMapping("/{id}")
    public Result<Object> delete(@PathVariable Integer id) {
        aiConfigService.delete(id);
        log.info("[AdminAiConfig] 删除配置: id={}", id);
        return Result.success();
    }

    @PutMapping("/{id}/default")
    public Result<Object> setDefault(@PathVariable Integer id) {
        aiConfigService.setDefault(id);
        log.info("[AdminAiConfig] 设为默认: id={}", id);
        return Result.success();
    }
}
