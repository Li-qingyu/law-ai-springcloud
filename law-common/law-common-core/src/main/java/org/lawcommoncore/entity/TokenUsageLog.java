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
public class TokenUsageLog implements Serializable {

    private Long id;

    private Integer userId;

    private String sessionId;

    private String provider;

    private String modelName;

    private Integer inputTokens;

    private Integer outputTokens;

    private Integer totalTokens;

    private String requestType;

    private Date createTime;
}
