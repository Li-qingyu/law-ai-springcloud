package org.lawuserservice.service;


import org.lawcommoncore.dto.*;
import org.lawcommoncore.entity.User;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.vo.LoginVO;

public  interface UserService {
    LoginVO login(UserLogin userLogin);

    PageResult list(UserPageQuery userPageQuery);


    Boolean register(UserRegisterDTO userRegisterDTO);

    void save(UserRegisterDTO userRegisterDTO);

    void update(UserDTO userDTO);

    void delete(Integer id);

    User get(Integer id);

    void updateStatus(Integer id, Integer status);

    /**
     * 分配角色（仅超级管理员），角色变更后会话需吊销强制重登
     */
    void updateRole(Integer id, Integer role);

    Integer count();

    Integer countOneWeekAgo();

    Integer resetPassword(ForgetFormDTO forgetFormDTO);
}
