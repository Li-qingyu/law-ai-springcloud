package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@AllArgsConstructor
@NoArgsConstructor
@Data
public class LawCaseVO  implements Serializable {
    private String typeName;
    private Long id;
    /**
     * 案例标题
     */
    private String title;
    /**
     * 法律类型ID（逻辑外键）
     */
    private Integer typeId;
    /**
     * 标签，多个标签用逗号分隔
     */
    private String tags;
    /**
     * 案例内容
     */
    private String content;
    /**
     * 封面图片URL
     */
    private String cover;
    /**
     * 发布时间
     */
    private LocalDateTime publishTime;
    /**
     * 状态：1-发布，0-下架
     */
    private Integer status;

}
