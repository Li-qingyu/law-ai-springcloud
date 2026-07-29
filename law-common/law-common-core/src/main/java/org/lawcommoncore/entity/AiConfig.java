package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.math.BigDecimal;
import java.util.Date;

@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class AiConfig implements Serializable {

    private Integer id;

    private String provider;

    private String modelName;

    private String apiKey;

    private String apiBaseUrl;

    private Integer isDefault;

    private Integer status;

    private Integer maxTokens;

    private BigDecimal temperature;

    private Date createTime;

    private Date updateTime;
}
