package org.lawuserservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.GuestConsultation;

import java.util.List;

@Mapper
public interface GuestConsultationMapper {

    void insert(GuestConsultation consultation);

    List<GuestConsultation> selectByGuestId(@Param("guestId") Integer guestId);

    void deleteByGuestId(@Param("guestId") Integer guestId);
}
