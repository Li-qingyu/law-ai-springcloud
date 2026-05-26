package org.lawuserservice.controller;

import lombok.extern.slf4j.Slf4j;
import org.apache.logging.log4j.util.PerformanceSensitive;
import org.lawcommoncore.dto.*;
import org.lawcommoncore.entity.User;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LoginVO;
import org.lawcommonsecurity.properties.JwtProperties;
import org.lawcommonsecurity.utils.JwtUtil;
import org.lawuserservice.service.EmailVerificationService;
import org.lawuserservice.service.UserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
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
        String token = jwtUtil.createJWT(jwtProperties.getAdminSecretKey(), jwtProperties.getAdminTtl(), claims);
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
        userService.resetPassword(forgetFormDTO);
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
     * 删除用户
     */
    @DeleteMapping("/admin/users/{id}")
    public Result delete(@PathVariable Integer id) {
        log.info("删除用户:{}", id);
        userService.delete(id);
        return Result.success("删除成功");
    }
    /**
     * 修改用户状态
     */
    @PostMapping("/admin/users/{id}/status")
    public Result updateStatus(@PathVariable Integer id, @RequestParam Integer status) {
        log.info("修改用户状态:{}, status:{}", id, status);
        userService.updateStatus(id, status);
        return Result.success("修改成功");
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
