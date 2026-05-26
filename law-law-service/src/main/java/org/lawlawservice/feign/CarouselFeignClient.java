package org.lawlawservice.feign;

import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.CarouselVO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@FeignClient(value = "law-common-service")
public interface CarouselFeignClient {
    @GetMapping("/user/home/carousel")
    Result<List<CarouselVO>> list() ;
}
