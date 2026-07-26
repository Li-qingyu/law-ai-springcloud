package org.lawuserservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.GuestUser;

@Mapper
public interface GuestUserMapper {

    GuestUser getByGuestKey(@Param("guestKey") String guestKey);

    GuestUser getById(@Param("id") Integer id);

    void insert(GuestUser guestUser);

    void updateById(GuestUser guestUser);

    void incrementQuestionCount(@Param("id") Integer id);
}
