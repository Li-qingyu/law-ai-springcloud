package org.lawcommonservice.feign;

import org.lawcommoncore.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(value = "law-law-service")
public interface LawFeignClient {

    @GetMapping("/admin/case/count")
    Result<Integer> getCaseCount();

    @GetMapping("/admin/case/countOneWeekAgo")
    Result<Integer> getCaseCountOneWeekAgo();

    @GetMapping("/admin/types/count")
    Result<Integer> getTypeCount();

    @GetMapping("/admin/types/countOneWeekAgo")
    Result<Integer> getTypeCountOneWeekAgo();

    @GetMapping("/admin/law-articles/count")
    Result<Integer> getArticleCount();

    @GetMapping("/admin/law-articles/countOneWeekAgo")
    Result<Integer> getArticleCountOneWeekAgo();
}
