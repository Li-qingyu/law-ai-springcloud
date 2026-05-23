package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;

/**
* 案例收藏表
* @TableName case_collection
*/
@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class CaseCollection implements Serializable {

    /**
    * 主键ID
    */
    private Integer id;
    /**
    * 用户ID（逻辑外键）
    */
    private Integer userId;
    /**
    * 案例ID（逻辑外键）
    */
    private Integer caseId;
    /**
    * 收藏时间
    */
    private Date createTime;


}
