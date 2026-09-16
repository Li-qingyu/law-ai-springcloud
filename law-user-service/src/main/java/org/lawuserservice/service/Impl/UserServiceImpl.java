package org.lawuserservice.service.Impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.annotation.RecordActivity;
import org.lawcommoncore.constant.PasswordConstant;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.*;
import org.lawcommoncore.entity.User;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.vo.LoginVO;
import org.lawcommonsecurity.annotation.RequireRole;
import org.lawcommonsecurity.constant.UserRole;
import org.lawuserservice.exception.RegisterException;
import org.lawuserservice.exception.UserException;
import org.lawuserservice.mapper.UserMapper;
import org.lawuserservice.service.EmailVerificationService;
import org.lawuserservice.service.UserService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.util.DigestUtils;

import java.time.LocalDateTime;

import static org.lawcommoncore.constant.ActivitiesConstant.*;

@Slf4j
@Service
public class UserServiceImpl implements UserService {
    @Autowired
    private UserMapper userMapper;
    @Autowired
    private EmailVerificationService emailVerificationService;

    @Override
    public LoginVO login(UserLogin userLogin) {
        String username = userLogin.getUsername();
        User user = userMapper.selectByUsername(username);
        String password = userLogin.getPassword();
        String md5Password = DigestUtils.md5DigestAsHex(password.getBytes());
        if (user != null && user.getPassword().equals(md5Password)&& user.getStatus() == 1) {
            return new LoginVO(user.getId(), user.getUsername(), user.getNickname(), user.getStatus(),"", user.getRole());
        }
        throw new UserException("用户名或密码错误");
    }

    @Override
    @RequireRole(UserRole.SUPER_ADMIN)
    public PageResult list(UserPageQuery userPageQuery) {
        PageHelper.startPage(userPageQuery.getPage(), userPageQuery.getPageSize());
        Page<User> page =  userMapper.list(userPageQuery);
        return new PageResult( page.getTotal(), page.getResult());
    }
    @RecordActivity(type = USER_REGISTER, titleTemplate = "'用户注册：' + #userRegisterDTO.username")
    @Override
    public Boolean register(UserRegisterDTO userRegisterDTO) {
        // 检查用户名是否已经存在
        if (userMapper.selectByUsername(userRegisterDTO.getUsername()) != null) {
            throw new RegisterException("用户名已经存在");
        }
        //检查邮箱是否已经存在
        Boolean isExist = userMapper.selectByEmail(userRegisterDTO.getEmail());
        if(isExist){
            throw new RegisterException("邮箱已经存在");
        }
        //检验邮箱的密码是否正确
        Boolean verifyCode = emailVerificationService.verifyCode(userRegisterDTO.getEmail(), userRegisterDTO.getEmailCode());
        if(!verifyCode){
            throw new RegisterException("邮箱验证码错误");
        }
        User user = new User();
        BeanUtils.copyProperties(userRegisterDTO, user);
        user.setUpdateTime(LocalDateTime.now());
        user.setCreateTime(LocalDateTime.now());
        user.setPassword(DigestUtils.md5DigestAsHex(user.getPassword().getBytes()));
        userMapper.insert(user);
        return true;
    }
    @RecordActivity(type = USER_ADD, titleTemplate = "'添加用户：' + #userRegisterDTO.username")
    @RequireRole(UserRole.SUPER_ADMIN)
    @Override
    public void  save(UserRegisterDTO userRegisterDTO) {
        User user = new User();
        BeanUtils.copyProperties(userRegisterDTO, user);
        user.setUpdateTime(LocalDateTime.now());
        user.setCreateTime(LocalDateTime.now());
        user.setPassword(DigestUtils.md5DigestAsHex(PasswordConstant.DEFAULT_PASSWORD.getBytes()));
        userMapper.insert(user);
    }

    @RecordActivity(type = USER_UPDATE, titleTemplate = "'更新用户：' + #userDTO.username")
    @Override
    public void update(UserDTO userDTO) {
        // 归属校验：非超级管理员只能修改自己的资料，防止普通用户/普通管理员借本接口篡改他人
        UserRole current = UserRole.of(BaseContext.getCurrentRole());
        if (current != UserRole.SUPER_ADMIN
                && (userDTO.getId() == null || !userDTO.getId().equals(BaseContext.getCurrentId()))) {
            throw new UserException("权限不足：只能修改本人的资料");
        }
        User user = new User();
        BeanUtils.copyProperties(userDTO, user);
        user.setUpdateTime(LocalDateTime.now());
        userMapper.update(user);
    }
    @RecordActivity(type = USER_DELETE, titleTemplate = "'删除id为' + #id + '的用户'")
    @RequireRole(UserRole.SUPER_ADMIN)
    @Override
    public void delete(Integer id) {
        //先检查id是否为空，在检查是否启用和存在
        if(id == null){
            throw new UserException("id不能为空");
        }
        User user = userMapper.get(id);
        if( user== null){
            throw new UserException("用户不存在");
        }
        if(user.getStatus() == 1){
            throw new UserException("用户已启用，请禁用之后在删除");
        }
        //TODO 查询与用户相关的数据


        userMapper.delete(id);
    }

    @Override
    public User get(Integer id) {
        //检查是否id为空
        if(id == null){
            throw new UserException("id不能为空");
        }
        return userMapper.get(id);
    }

    @Override
    @RequireRole(UserRole.SUPER_ADMIN)
    public void updateStatus(Integer id, Integer status) {
        if(id == null){
            throw new UserException("id不能为空");
        }
        if(status == null){
            throw new UserException("status不能为空");
        }
        User user = new User();
        user.setId(id);
        user.setUpdateTime(LocalDateTime.now());
        user.setStatus(status);
        userMapper.update(user);

    }

    /**
     * 分配角色：校验角色值合法后写入；调用方（Controller）负责吊销该用户的 Redis 会话强制重登
     */
    @Override
    @RequireRole(UserRole.SUPER_ADMIN)
    public void updateRole(Integer id, Integer role) {
        if (id == null) {
            throw new UserException("id不能为空");
        }
        if (role == null || (role != 0 && role != 1 && role != 2)) {
            throw new UserException("非法的角色值：" + role);
        }
        User user = new User();
        user.setId(id);
        user.setUpdateTime(LocalDateTime.now());
        user.setRole(role);
        userMapper.update(user);
        log.info("用户角色{}",user.getRole());
        log.info("用户角色已变更 userId={}, role={}", id, role);
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Integer count() {
        return userMapper.count();
    }

    @Override
    @RequireRole({UserRole.ADMIN, UserRole.SUPER_ADMIN})
    public Integer countOneWeekAgo() {
        return userMapper.countOneWeekAgo();
    }

    @Override
    public Integer resetPassword(ForgetFormDTO forgetFormDTO) {
        //检查用户名和邮箱是否正确
        User user = userMapper.selectByUsername(forgetFormDTO.getUsername());
        if(user == null){
            throw new UserException("用户名不存在，重新输入");
        }
        if(!forgetFormDTO.getEmail().equals(user.getEmail())){
            throw new UserException("用户名或邮箱错误,请重新输入");
        }
        Boolean verifyCode = emailVerificationService.verifyCode(forgetFormDTO.getEmail(), forgetFormDTO.getEmailCode());
        if(!verifyCode){
            throw new UserException("邮箱验证码错误");
        }
        user.setPassword(DigestUtils.md5DigestAsHex(forgetFormDTO.getPassword().getBytes()));
        user.setUpdateTime(LocalDateTime.now());
        userMapper.update(user);
        return user.getId();
    }


}
