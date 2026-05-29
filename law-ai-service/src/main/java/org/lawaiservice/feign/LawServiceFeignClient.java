package org.lawaiservice.feign;

import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LawCaseVO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(value = "law-law-service")
public interface LawServiceFeignClient {

    /**
     * 根据ID获取法律条文
     */
    @GetMapping("/internal/law-articles/{id}")
    Result<LawArticle> getLawArticle(@PathVariable("id") Long id);

    /**
     * 根据ID和类型ID获取案例卡片
     */
    @GetMapping("/internal/cases/card")
    Result<LawCaseVO> getLawCaseCard(@RequestParam("id") Long id, @RequestParam("typeId") Integer typeId);
}
