package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;

@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class UserTokenQuota implements Serializable {

    private Integer id;

    private Integer userId;

    private Long dailyLimit;

    private Long monthlyLimit;

    private Long totalLimit;

    private Long dailyUsed;

    private Long monthlyUsed;

    private Long totalUsed;

    private Date lastResetDaily;

    private String lastResetMonthly;

    private Date createTime;

    private Date updateTime;
}
