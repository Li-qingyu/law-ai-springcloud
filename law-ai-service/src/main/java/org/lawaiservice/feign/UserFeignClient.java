package org.lawaiservice.feign;

import org.lawcommoncore.entity.User;
import org.lawcommoncore.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@FeignClient(value = "law-user-service", contextId = "userFeignClient")
public interface UserFeignClient {

    @GetMapping("/admin/users/{id}")
    Result<User> getUserById(@PathVariable("id") Integer id);
}
