package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ModelUsageVO implements Serializable {
    private String provider;
    private String modelName;
    private Long totalTokens;
    private Long inputTokens;
    private Long outputTokens;
}
