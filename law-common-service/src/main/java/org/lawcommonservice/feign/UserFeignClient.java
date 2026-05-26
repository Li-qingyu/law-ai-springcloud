package org.lawcommonservice.feign;

import org.lawcommoncore.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

@FeignClient(value = "law-user-service")
public interface UserFeignClient {

    @GetMapping("/admin/users/count")
    Result<Integer> getUserCount();

    @GetMapping("/admin/users/countOneWeekAgo")
    Result<Integer> getUserCountOneWeekAgo();
}
