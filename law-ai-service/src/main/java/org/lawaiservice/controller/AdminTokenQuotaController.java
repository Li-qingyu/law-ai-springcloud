package org.lawaiservice.controller;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.mapper.TokenUsageLogMapper;
import org.lawaiservice.mapper.UserTokenQuotaMapper;
import org.lawaiservice.service.TokenQuotaService;
import org.lawcommoncore.dto.TokenQuotaUpdateDTO;
import org.lawcommoncore.entity.TokenUsageLog;
import org.lawcommoncore.entity.UserTokenQuota;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.DailyTokenStatsVO;
import org.lawcommoncore.vo.DailyTokenUsageVO;
import org.lawcommoncore.vo.ModelUsageVO;
import org.lawcommoncore.vo.TokenStatsVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;

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
    public Result<Object> updateQuota(@PathVariable Integer userId, @RequestBody TokenQuotaUpdateDTO dto) {
        log.info("[AdminToken] 修改用户配额: userId={}", userId);
        UserTokenQuota quota = userTokenQuotaMapper.selectByUserId(userId);
        if (quota == null) {
            return Result.error("用户配额不存在");
        }
        if (dto.getDailyLimit() != null) quota.setDailyLimit(dto.getDailyLimit());
        if (dto.getMonthlyLimit() != null) quota.setMonthlyLimit(dto.getMonthlyLimit());
        if (dto.getTotalLimit() != null) quota.setTotalLimit(dto.getTotalLimit());
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

    @GetMapping("/stats/summary")
    public Result<TokenStatsVO> statsSummary() {
        log.info("[AdminToken] 统计概览");
        LocalDate today = LocalDate.now();
        LocalDate monthStart = today.withDayOfMonth(1);
        Date todayStart = Date.from(today.atStartOfDay(ZoneId.systemDefault()).toInstant());
        Date monthStartDate = Date.from(monthStart.atStartOfDay(ZoneId.systemDefault()).toInstant());
        Date now = Date.from(LocalDateTime.now().atZone(ZoneId.systemDefault()).toInstant());

        Date last7Start = Date.from(today.minusDays(7).atStartOfDay(ZoneId.systemDefault()).toInstant());
        Date last30Start = Date.from(today.minusDays(30).atStartOfDay(ZoneId.systemDefault()).toInstant());

        Long todayTokens = tokenUsageLogMapper.sumDailyTokens(todayStart, now);
        Long monthTokens = tokenUsageLogMapper.sumMonthlyTokens(monthStartDate, now);
        Long allTokens = tokenUsageLogMapper.sumAllTokens();
        Long tokens7d = tokenUsageLogMapper.sumTokensBetween(last7Start, now);
        Long tokens30d = tokenUsageLogMapper.sumTokensBetween(last30Start, now);
        Integer userCount = tokenUsageLogMapper.countDistinctUsersToday(todayStart);
        long avgDaily = userCount > 0 ? todayTokens / userCount : 0;

        TokenStatsVO vo = TokenStatsVO.builder()
                .totalTokensToday(todayTokens)
                .totalTokensMonth(monthTokens)
                .totalTokensLast7Days(tokens7d)
                .totalTokensLast30Days(tokens30d)
                .totalTokensAll(allTokens)
                .avgDailyPerUser(avgDaily)
                .activeUsersToday(userCount)
                .build();

        return Result.success(vo);
    }

    @GetMapping("/stats/models")
    public Result<List<ModelUsageVO>> statsModels() {
        log.info("[AdminToken] 模型使用分布");
        LocalDate today = LocalDate.now();
        Date monthStart = Date.from(today.withDayOfMonth(1).atStartOfDay(ZoneId.systemDefault()).toInstant());
        Date now = Date.from(LocalDateTime.now().atZone(ZoneId.systemDefault()).toInstant());
        List<ModelUsageVO> models = tokenUsageLogMapper.groupByModel(monthStart, now);
        return Result.success(models);
    }

    @GetMapping("/stats/daily")
    public Result<DailyTokenStatsVO> statsDaily() {
        log.info("[AdminToken] 每日用量趋势");
        LocalDate today = LocalDate.now();
        Date now = Date.from(LocalDateTime.now().atZone(ZoneId.systemDefault()).toInstant());
        Date last7Start = Date.from(today.minusDays(7).atStartOfDay(ZoneId.systemDefault()).toInstant());
        Date last30Start = Date.from(today.minusDays(30).atStartOfDay(ZoneId.systemDefault()).toInstant());

        List<DailyTokenUsageVO> last7Days = tokenUsageLogMapper.sumTokensGroupByDay(last7Start, now);
        List<DailyTokenUsageVO> last30Days = tokenUsageLogMapper.sumTokensGroupByDay(last30Start, now);

        DailyTokenStatsVO vo = DailyTokenStatsVO.builder()
                .last7Days(last7Days)
                .last30Days(last30Days)
                .build();

        return Result.success(vo);
    }
}
