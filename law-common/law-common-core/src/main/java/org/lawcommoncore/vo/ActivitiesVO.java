package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ActivitiesVO implements Serializable {
    private Integer id;
    private String type;           // 活动类型
    private String title;          // 活动标题
    private String userName;       // 操作人姓名
    private LocalDateTime time;    // 操作时间
}
