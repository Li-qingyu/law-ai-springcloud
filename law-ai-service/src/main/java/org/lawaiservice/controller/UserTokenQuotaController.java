package org.lawaiservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawaiservice.service.TokenQuotaService;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.entity.UserTokenQuota;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.TokenQuotaVO;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/user/ai/token")
@Slf4j
public class UserTokenQuotaController {

    @Autowired
    private TokenQuotaService tokenQuotaService;

    @GetMapping("/quota")
    public Result<TokenQuotaVO> getMyQuota() {
        Integer userId = BaseContext.getCurrentId();
        log.info("[UserToken] 查看个人配额: userId={}", userId);

        UserTokenQuota quota = tokenQuotaService.getQuota(userId);

        TokenQuotaVO vo = TokenQuotaVO.builder()
                .userId(quota.getUserId())
                .dailyLimit(quota.getDailyLimit())
                .dailyUsed(quota.getDailyUsed())
                .dailyRemain(quota.getDailyLimit() > 0 ? quota.getDailyLimit() - quota.getDailyUsed() : -1L)
                .monthlyLimit(quota.getMonthlyLimit())
                .monthlyUsed(quota.getMonthlyUsed())
                .monthlyRemain(quota.getMonthlyLimit() > 0 ? quota.getMonthlyLimit() - quota.getMonthlyUsed() : -1L)
                .totalLimit(quota.getTotalLimit())
                .totalUsed(quota.getTotalUsed())
                .totalRemain(quota.getTotalLimit() > 0 ? quota.getTotalLimit() - quota.getTotalUsed() : -1L)
                .build();

        return Result.success(vo);
    }
}
