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
public class TokenQuotaVO implements Serializable {
    private Integer userId;
    private Long dailyLimit;
    private Long dailyUsed;
    private Long dailyRemain;
    private Long monthlyLimit;
    private Long monthlyUsed;
    private Long monthlyRemain;
    private Long totalLimit;
    private Long totalUsed;
    private Long totalRemain;
}
