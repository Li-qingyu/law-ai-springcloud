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

    Integer count();

    Integer countOneWeekAgo();

    Integer resetPassword(ForgetFormDTO forgetFormDTO);
}
