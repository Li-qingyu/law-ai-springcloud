package org.lawuserservice.controller;

import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.entity.GuestUser;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.GuestInfoVO;
import org.lawcommoncore.vo.GuestInitVO;
import org.lawcommonredis.utils.RedisUtil;
import org.lawcommonsecurity.properties.JwtProperties;
import org.lawcommonsecurity.utils.JwtUtil;
import org.lawuserservice.service.GuestUserService;
import org.lawuserservice.util.IpUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

@RestController
@Slf4j
public class GuestController {

    /**
     * 一个 IP 一个游客：IP → guestKey 的 Redis 映射前缀
     */
    private static final String GUEST_IP_MAPPING_KEY_PREFIX = "guest:ip:";

    /**
     * IP 映射缓存时长（秒），默认 30 天
     */
    private static final long GUEST_IP_MAPPING_TTL = 30 * 24 * 3600L;

    @Autowired
    private GuestUserService guestUserService;
    @Autowired
    private JwtProperties jwtProperties;
    @Autowired
    private JwtUtil jwtUtil;
    @Autowired
    private RedisUtil redisUtil;

    @PostMapping("/guest/init")
    public Result<GuestInitVO> init(@RequestParam String guestKey, HttpServletRequest request) {
        log.info("游客初始化: guestKey={}", guestKey);

        String ipAddress = IpUtil.getClientIp(request);
        String userAgent = request.getHeader("User-Agent");

        // 同一 IP 复用已映射的游客，避免清 localStorage / 无痕窗口重开无限重置提问额度
        String mappingKey = GUEST_IP_MAPPING_KEY_PREFIX + ipAddress;
        GuestUser guest = null;
        Object mappedGuestKey = redisUtil.get(mappingKey);
        if (mappedGuestKey != null) {
            guest = guestUserService.getByGuestKey(mappedGuestKey.toString());
        }
        if (guest == null) {
            guest = guestUserService.init(guestKey, ipAddress, userAgent);
            redisUtil.set(mappingKey, guest.getGuestKey(), GUEST_IP_MAPPING_TTL);
            log.info("已建立游客 IP 映射: ip={}, guestKey={}", ipAddress, guest.getGuestKey());
        }

        Map<String, Object> claims = new HashMap<>();
        claims.put("guestId", guest.getId());
        claims.put("guestKey", guest.getGuestKey());
        claims.put("type", "guest");
        String token = jwtUtil.createJWT(jwtProperties.getAdminSecretKey(), 7 * 24 * 3600 * 1000L, claims);

        GuestInitVO vo = new GuestInitVO(guest.getId(), guest.getGuestKey(), guest.getQuestionCount(), guest.getMaxQuestion(), token);
        return Result.success(vo);
    }

    @GetMapping("/guest/info")
    public Result<GuestInfoVO> info(@RequestParam String guestKey) {
        log.info("获取游客信息: guestKey={}", guestKey);

        GuestUser guest = guestUserService.getByGuestKey(guestKey);
        if (guest == null) {
            return Result.error("游客信息不存在");
        }

        GuestInfoVO vo = new GuestInfoVO(guest.getId(), guest.getGuestKey(), guest.getQuestionCount(), guest.getMaxQuestion());
        return Result.success(vo);
    }

    @GetMapping("/guest/canAsk")
    public Result<Boolean> canAsk(@RequestParam Integer guestId) {
        return Result.success(guestUserService.canAsk(guestId));
    }

    @PostMapping("/guest/incrementCount")
    public Result incrementCount(@RequestParam Integer guestId) {
        guestUserService.incrementQuestionCount(guestId);
        return Result.success();
    }

    @PostMapping("/guest/delete")
    public Result deleteGuest(@RequestParam Integer guestId) {
        log.info("删除游客: guestId={}", guestId);
        guestUserService.deleteByGuestId(guestId);
        return Result.success();
    }
}
