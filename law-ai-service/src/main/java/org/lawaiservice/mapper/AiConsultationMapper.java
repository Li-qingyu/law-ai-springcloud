package org.lawaiservice.mapper;

import com.github.pagehelper.Page;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.vo.AiConsultationDetailVO;
import org.lawcommoncore.vo.AiSessionHistoryVO;
import org.lawcommoncore.vo.SearchResultVO;

import java.util.List;

@Mapper
public interface AiConsultationMapper {
    /**
     * 搜索AI咨询记录
     * @param keyword 关键词
     * @return 搜索结果列表
     */
    Page<SearchResultVO> searchConsultationByKeyword(@Param("keyword") String keyword);

    /**
     * 根据会话ID查询咨询记录
     * @param sessionId 会话ID
     * @return 咨询记录列表
     */
    AiConsultation selectBySessionId(@Param("sessionId") String sessionId);

    /**
     * 插入咨询记录
     * @param consultation 咨询记录实体
     * @return 影响的行数
     */
    int insert(AiConsultation consultation);

    AiConsultation get(Integer id);


    List<AiSessionHistoryVO> getAllSession( @Param("userId") Integer userId);

    List<AiConsultationDetailVO> chatDetail(String sessionId);

    void delete(String sessionId);
}