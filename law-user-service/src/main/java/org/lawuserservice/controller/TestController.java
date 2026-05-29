package org.lawuserservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.result.Result;
//import org.lawcommonoss.utils.AliOssUtil;
import org.lawcommonredis.utils.RedisUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/test")
@Slf4j
public class TestController {

    @Autowired
    private RedisUtil redisUtil;

//    @Autowired
//    private AliOssUtil aliOssUtil;
    /**
     * 测试公共模块是否生效
     * GET /api/test/common
     */
    @GetMapping("/common")
    public Map<String, Object> testCommon() {
        Map<String, Object> result = new HashMap<>();

        // 1. 测试 law-common-core: BaseContext (用户上下文)
        Integer userId = BaseContext.getCurrentId();
        result.put("userId", userId);
        result.put("message", userId != null ? "用户已登录" : "用户未登录(可能白名单)");

        // 2. 测试 law-common-redis: Redis 读写
        String testKey = "test:common:module";
        String testValue = "hello-common-" + System.currentTimeMillis();
        redisUtil.set(testKey, testValue, 60);
        String readBack = (String) redisUtil.get(testKey);
        result.put("redis_write", testValue);
        result.put("redis_read", readBack);
        result.put("redis_ok", testValue.equals(readBack));

        return result;
    }

    /**
     * 测试白名单接口（不需要token）
     * GET /api/test/public
     */
    @GetMapping("/public")
    public Map<String, String> testPublic() {
        Map<String, String> result = new HashMap<>();
        result.put("status", "ok");
        result.put("message", "白名单接口，无需token");
        return result;
    }
//    @PostMapping("/oss")
//    public Result testOss(MultipartFile file) throws IOException {
//        //测试Oss模块
//        log.info("文件上传：{}", file.getOriginalFilename());
//        String url = aliOssUtil.upload(file.getBytes(), file.getOriginalFilename());
//        log.info("文件上传成功：{}", url);
//        return Result.success(url);
//    }
}
