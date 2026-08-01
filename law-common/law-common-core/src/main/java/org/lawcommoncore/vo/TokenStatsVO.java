package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class TokenStatsVO implements Serializable {
    private Long totalTokensToday;
    private Long totalTokensMonth;
    private Long totalTokensAll;
    private Long totalTokensLast7Days;
    private Long totalTokensLast30Days;
    private Long avgDailyPerUser;
    private Integer activeUsersToday;
}
