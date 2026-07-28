package org.lawaiservice.controller;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.mapper.TokenUsageLogMapper;
import org.lawaiservice.mapper.UserTokenQuotaMapper;
import org.lawaiservice.service.TokenQuotaService;
import org.lawcommoncore.entity.TokenUsageLog;
import org.lawcommoncore.entity.UserTokenQuota;
import org.lawcommoncore.result.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/admin/token")
@Slf4j
public class AdminTokenQuotaController {

    @Autowired
    private TokenQuotaService tokenQuotaService;

    @Autowired
    private UserTokenQuotaMapper userTokenQuotaMapper;

    @Autowired
    private TokenUsageLogMapper tokenUsageLogMapper;

    @GetMapping("/quota/{userId}")
    public Result<UserTokenQuota> getQuota(@PathVariable Integer userId) {
        log.info("[AdminToken] 查看用户配额: userId={}", userId);
        UserTokenQuota quota = userTokenQuotaMapper.selectByUserId(userId);
        if (quota == null) {
            return Result.error("用户配额不存在");
        }
        return Result.success(quota);
    }

    @PutMapping("/quota/{userId}")
    public Result<Object> updateQuota(@PathVariable Integer userId, @RequestBody Map<String, Long> body) {
        log.info("[AdminToken] 修改用户配额: userId={}", userId);
        UserTokenQuota quota = userTokenQuotaMapper.selectByUserId(userId);
        if (quota == null) {
            return Result.error("用户配额不存在");
        }
        if (body.containsKey("dailyLimit")) quota.setDailyLimit(body.get("dailyLimit"));
        if (body.containsKey("monthlyLimit")) quota.setMonthlyLimit(body.get("monthlyLimit"));
        if (body.containsKey("totalLimit")) quota.setTotalLimit(body.get("totalLimit"));
        userTokenQuotaMapper.updateLimit(quota);
        return Result.success();
    }

    @PostMapping("/quota/reset/{userId}")
    public Result<Object> resetQuota(@PathVariable Integer userId) {
        log.info("[AdminToken] 重置用户配额: userId={}", userId);
        tokenQuotaService.resetUser(userId);
        return Result.success();
    }

    @GetMapping("/quota/list")
    public Result<PageInfo<UserTokenQuota>> listQuota(
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        log.info("[AdminToken] 配额列表: page={}, pageSize={}", page, pageSize);
        PageHelper.startPage(page, pageSize);
        List<UserTokenQuota> list = userTokenQuotaMapper.selectList();
        PageInfo<UserTokenQuota> pageInfo = new PageInfo<>(list);
        return Result.success(pageInfo);
    }

    @GetMapping("/usage/log")
    public Result<PageInfo<TokenUsageLog>> listUsageLog(
            @RequestParam(required = false) Integer userId,
            @RequestParam(defaultValue = "1") int page,
            @RequestParam(defaultValue = "10") int pageSize) {
        log.info("[AdminToken] 使用日志: userId={}, page={}, pageSize={}", userId, page, pageSize);
        PageHelper.startPage(page, pageSize);
        List<TokenUsageLog> list = tokenUsageLogMapper.selectList(userId);
        PageInfo<TokenUsageLog> pageInfo = new PageInfo<>(list);
        return Result.success(pageInfo);
    }
}
