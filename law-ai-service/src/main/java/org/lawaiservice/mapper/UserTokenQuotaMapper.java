package org.lawaiservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.lawcommoncore.entity.UserTokenQuota;

import java.util.List;

@Mapper
public interface UserTokenQuotaMapper {

    UserTokenQuota selectByUserId(Integer userId);

    int insert(UserTokenQuota quota);

    int initQuota(Integer userId);

    int updateUsage(@Param("userId") Integer userId,
                    @Param("inputTokens") int inputTokens,
                    @Param("outputTokens") int outputTokens,
                    @Param("totalTokens") int totalTokens);

    int updateLimit(UserTokenQuota quota);

    int resetDaily(Integer userId);

    int resetMonthly(@Param("userId") Integer userId,
                     @Param("month") String month);

    /** 批量重置所有用户每日用量 */
    int resetAllDaily();

    /** 批量重置所有用户每月用量 */
    int resetAllMonthly(@Param("month") String month);

    List<UserTokenQuota> selectList();
}
