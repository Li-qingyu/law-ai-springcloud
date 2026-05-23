package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AiSessionHistoryVO {
    private Integer id;
    private String sessionId;
    private String title;
    private String content;
    private String createTime;
}
