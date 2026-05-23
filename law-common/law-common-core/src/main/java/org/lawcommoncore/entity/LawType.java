package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* 法律类型表
* @TableName law_type
*/
@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class LawType implements Serializable {

    /**
    * 主键ID
    */
    private Integer id;
    /**
    * 类型名称
    */
    private String name;
    /**
    * 类型描述
    */
    private String description;
    /**
    * 创建时间
    */
    private LocalDateTime createTime;
    /**
    * 更新时间
    */
    private LocalDateTime updateTime;


}
