package org.lawaiservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.GuestConsultation;
import org.lawcommoncore.vo.AiConsultationDetailVO;
import org.lawcommoncore.vo.AiSessionHistoryVO;

import java.util.List;

@Mapper
public interface GuestConsultationMapper {

    void insert(GuestConsultation consultation);

    List<GuestConsultation> selectByGuestId(@Param("guestId") Integer guestId);

    List<AiSessionHistoryVO> getAllGuestSession(@Param("guestId") Integer guestId);

    List<AiConsultationDetailVO> guestChatDetail(@Param("sessionId") String sessionId);

    void deleteGuestSession(@Param("sessionId") String sessionId);

    void deleteByGuestId(@Param("guestId") Integer guestId);
}
