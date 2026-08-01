package org.lawaiservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.TokenUsageLog;

import java.util.Date;
import java.util.List;
import org.lawcommoncore.vo.ModelUsageVO;
import org.lawcommoncore.vo.DailyTokenUsageVO;
@Mapper
public interface TokenUsageLogMapper {

    int insert(TokenUsageLog log);

    Long sumDailyTokens(@Param("startTime") Date startTime,
                        @Param("endTime") Date endTime);

    Long sumMonthlyTokens(@Param("startTime") Date startTime,
                          @Param("endTime") Date endTime);

    Long sumUserTokens(@Param("userId") Integer userId,
                       @Param("startTime") Date startTime,
                       @Param("endTime") Date endTime);

    List<TokenUsageLog> selectList(@Param("userId") Integer userId);

    Long sumAllTokens();

    List<ModelUsageVO> groupByModel(@Param("startTime") Date startTime,
                                    @Param("endTime") Date endTime);

    Integer countDistinctUsersToday(@Param("startTime") Date startTime);

    Long sumTokensBetween(@Param("startTime") Date startTime,
                          @Param("endTime") Date endTime);

    List<DailyTokenUsageVO> sumTokensGroupByDay(@Param("startTime") Date startTime,
                                                 @Param("endTime") Date endTime);
}
