package org.lawuserservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.apache.logging.log4j.util.PerformanceSensitive;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.*;
import org.lawcommoncore.entity.User;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LoginVO;
import org.lawcommonredis.utils.RedisUtil;
import org.lawcommonsecurity.constant.TokenConstant;
import org.lawcommonsecurity.properties.JwtProperties;
import org.lawcommonsecurity.utils.JwtUtil;
import org.lawuserservice.service.EmailVerificationService;
import org.lawuserservice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@RestController
@Slf4j
public class UserController {

    @Autowired
    private UserService userService;
    @Autowired
    private EmailVerificationService emailVerificationService;
    @Autowired
    private JwtProperties jwtProperties;
    @Autowired
    private JwtUtil jwtUtil;
    @Autowired
    private RedisUtil redisUtil;
    /**
     * 登录
     * @param userLogin
     * @return
     */
    @PostMapping("/login")
    public Result login(@RequestBody UserLogin userLogin) {
        log.info("用户登录{}", userLogin);
        LoginVO loginVO = userService.login(userLogin);
        Map<String,Object> claims=new HashMap<>();
        claims.put("userId", loginVO.getId());
        claims.put("role", loginVO.getRole());
        claims.put("type", "user");
        String token = jwtUtil.createJWT(jwtProperties.getAdminSecretKey(), jwtProperties.getAdminTtl(), claims);
        // 登录成功后，将当前 token 写入 Redis 会话缓存，后续每次请求比对
        long ttlSeconds = jwtProperties.getAdminTtl() > 0 ? jwtProperties.getAdminTtl() / 1000 : TokenConstant.DEFAULT_CACHE_TTL_SECONDS;
        redisUtil.set(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + loginVO.getId(), token, ttlSeconds);
        loginVO.setToken(token);
        return Result.success(loginVO);
    }
    /**
     * 发送验证码
     */
    @PostMapping("/sendEmailCode")
    public Result sendEmailCode(@RequestBody UserRegisterDTO userRegisterDTO) {
        log.info("发送验证码{}", userRegisterDTO);
        String email = userRegisterDTO.getEmail();
        String msg = emailVerificationService.sendVerificationCode(email);
        if(msg.startsWith("发送失败")) {
            return Result.error(msg);
        } else if (msg.equals("邮箱格式不正确")) {
            return Result.error(msg);
        }
        return Result.success(msg);
    }
    /**
     * 忘记密码
     */
    @PostMapping("/resetPassword")
    public Result resetPassword(@RequestBody ForgetFormDTO forgetFormDTO) {
        log.info("忘记密码{}", forgetFormDTO);
        Integer userId = userService.resetPassword(forgetFormDTO);
        // 改密成功后吊销该用户旧 token，强制重新登录
        if (userId != null) {
            redisUtil.delete(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + userId);
            log.info("重置密码成功，已吊销该用户会话缓存 userId:{}", userId);
        }
        return Result.success("修改密码成功");
    }

    /**
     * 注册
     * @param userRegisterDTO
     * @return
     */
    @PostMapping("/register")
    public Result register(@RequestBody UserRegisterDTO userRegisterDTO) {
        log.info("用户注册{}", userRegisterDTO);
        Boolean success = userService.register(userRegisterDTO);
        if( success){
            return Result.success("注册成功");
        }else{
            return Result.error("注册失败");
        }
    }

    /**
     * 分页查询
     */
    @GetMapping("/admin/users")
    public Result<PageResult> list(UserPageQuery userPageQuery) {
        log.info("分页查询用户列表:{}", userPageQuery);
        PageResult pageResult = userService.list(userPageQuery);
        return Result.success(pageResult);
    }
    /**
     * 添加用户
     */
    @PostMapping("/admin/users")
    public Result add(@RequestBody UserRegisterDTO userRegisterDTO) {
        log.info("添加用户:{}", userRegisterDTO);
       userService.save(userRegisterDTO);
        return Result.success("添加成功");
    }
    /**
     * 修改用户
     */
    @PutMapping("/admin/users")
    public Result update(@RequestBody UserDTO userDTO) {
        log.info("修改用户:{}", userDTO);
        userService.update(userDTO);
        return Result.success("更新成功");
    }
    /**
     * 根据id查询用户
     */
    @GetMapping("/admin/users/{id}")
    public Result<User> get(@PathVariable Integer id) {
        log.info("查询用户:{}", id);
        User user = userService.get(id);
        return Result.success( user);
    }
    /**
     * 退出登录
     * 删除当前用户 Redis 中的 token 会话缓存，使现有 token 立即失效
     */
    @PostMapping("/logout")
    public Result logout() {
        Integer userId = BaseContext.getCurrentId();
        if (userId != null) {
            redisUtil.delete(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + userId);
            log.info("用户退出登录，已清除会话缓存 userId:{}", userId);
        }
        return Result.success("退出成功");
    }

    /**
     * 删除用户（支持逗号分隔批量删除），同时清除对应 Redis 会话缓存
     */
    @DeleteMapping("/admin/users/{ids}")
    public Result delete(@PathVariable("ids") List<Integer> ids) {
        log.info("删除用户:{}", ids);
        for (Integer userId : ids) {
            userService.delete(userId);
            redisUtil.delete(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + userId);
        }
        return Result.success("删除成功");
    }
    /**
     * 修改用户状态
     */
    @PostMapping("/admin/users/{id}/status")
    public Result updateStatus(@PathVariable Integer id, @RequestParam Integer status) {
        log.info("修改用户状态:{}, status:{}", id, status);
        userService.updateStatus(id, status);
        // 禁用用户时吊销其全部会话，禁止继续访问
        if (status != null && status == 0) {
            redisUtil.delete(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + id);
            log.info("用户已被禁用，已吊销会话缓存 userId:{}", id);
        }
        return Result.success("修改成功");
    }

    /**
     * 分配角色（仅超级管理员，由服务层 @RequireRole 校验）
     * 角色变更后删除该用户会话缓存，强制重新登录以刷新 JWT 中的 role
     */
    @PutMapping("/admin/users/{id}/role")
    public Result updateRole(@PathVariable Integer id, @RequestParam Integer role) {
        log.info("分配角色:{}, role:{}", id, role);
        userService.updateRole(id, role);
        // 角色写入 JWT，旧 token 携带旧角色，必须吊销会话强制重登
        redisUtil.delete(TokenConstant.USER_TOKEN_REDIS_KEY_PREFIX + id);
        log.info("角色已变更，已吊销会话缓存 userId:{}", id);
        return Result.success("分配成功");
    }
    /**
     * 统计总用户
     */
    @GetMapping("/admin/users/count")
    public Result<Integer> count() {
        log.info("统计总用户");
        Integer count = userService.count();
        return Result.success(count);
    }
    @GetMapping("/admin/users/countOneWeekAgo")
    public Result<Integer> countOneWeekAgo() {
        log.info("统计一周前用户数");
        Integer count = userService.countOneWeekAgo();
        return Result.success(count);
    }


}
