package org.lawaiservice.feign;

import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.GuestInfoVO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestParam;

@FeignClient(value = "law-user-service")
public interface GuestFeignClient {

    @GetMapping("/guest/canAsk")
    Result<Boolean> canAsk(@RequestParam("guestId") Integer guestId);

    @PostMapping("/guest/incrementCount")
    Result incrementCount(@RequestParam("guestId") Integer guestId);

    @GetMapping("/guest/info")
    Result<GuestInfoVO> getGuestInfo(@RequestParam("guestKey") String guestKey);

    @PostMapping("/guest/delete")
    Result deleteGuest(@RequestParam("guestId") Integer guestId);
}
