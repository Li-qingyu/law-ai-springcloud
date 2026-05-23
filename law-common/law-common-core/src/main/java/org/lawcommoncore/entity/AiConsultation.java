package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;
/**
* AI咨询记录表
* @TableName ai_consultation
*/
@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class AiConsultation implements Serializable {

    /**
    * 主键ID
    */
    private Integer id;
    /**
    * 会话ID
    */
    private String sessionId;
    /**
    * 会话中的轮次顺序
    */
    private Integer turnNumber;
    /**
    * 用户ID（逻辑外键）
    */
    private Integer userId;
    /**
    * 问题
    */
    private String question;
    /**
    * 回答
    */
    private String answer;
    /**
    * 咨询时间
    */
    private Date createTime;
    /**
    * 数据卡片JSON数组，存储该轮问答使用的参考数据
    */
    private String dataCards;


}
