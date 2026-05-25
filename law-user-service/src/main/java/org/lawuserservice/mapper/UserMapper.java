package org.lawuserservice.mapper;

import com.github.pagehelper.Page;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;
import org.lawcommoncore.dto.UserPageQuery;
import org.lawcommoncore.entity.User;
import org.mybatis.spring.annotation.MapperScan;

@Mapper
public interface UserMapper {


    User selectByUsername(String username);

    Page<User> list(UserPageQuery userPageQuery);

    void insert(User user);

    Boolean selectByEmail(String email);

    void update(User user);

    User get(Integer id);

    void delete(Integer id);
    @Select("select count(*) from user")
    Integer count();
    @Select("select count(*) from user where create_time < DATE_SUB(NOW(),  INTERVAL 7 DAY)")
    Integer countOneWeekAgo();
}
