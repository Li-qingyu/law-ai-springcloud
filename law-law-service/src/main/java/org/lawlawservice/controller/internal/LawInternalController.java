package org.lawlawservice.controller.internal;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LawCaseVO;
import org.lawlawservice.service.LawArticleService;
import org.lawlawservice.service.LawCaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/internal")
public class LawInternalController {

    @Autowired
    private LawArticleService lawArticleService;

    @Autowired
    private LawCaseService lawCaseService;

    /**
     * 根据ID获取法律条文（供其他微服务调用）
     */
    @GetMapping("/law-articles/{id}")
    public Result<LawArticle> getLawArticle(@PathVariable Long id) {
        log.info("内部调用-获取法律条文: {}", id);
        LawArticle lawArticle = lawArticleService.get(id);
        return Result.success(lawArticle);
    }

    /**
     * 根据ID和类型ID获取案例卡片（供其他微服务调用）
     */
    @GetMapping("/cases/card")
    public Result<LawCaseVO> getLawCaseCard(@RequestParam Long id, @RequestParam Integer typeId) {
        log.info("内部调用-获取案例卡片: id={}, typeId={}", id, typeId);
        LawCaseVO lawCaseVO = lawCaseService.getCard(id, typeId);
        return Result.success(lawCaseVO);
    }
}
