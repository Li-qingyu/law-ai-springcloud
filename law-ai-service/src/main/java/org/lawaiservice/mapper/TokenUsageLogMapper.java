package org.lawaiservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.TokenUsageLog;

import java.util.Date;
import java.util.List;
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
}
