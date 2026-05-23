package org.lawcommoncore.entity;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;
import java.util.Date;

/**
* 法律条文表
* @TableName law_article
*/
@Data
@AllArgsConstructor
@Builder
@NoArgsConstructor
public class LawArticle implements Serializable {

    /**
    * 主键ID
    */
    private Long id;
    /**
    * 法律书标题
    */
    private String bookTitle;
    private Integer lawBookId;
    /**
    * 法律条文标题
    */
    private String articleTitle;
    /**
    * 条文内容
    */
    private String content;
    /**
    * 发布日期
    */
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date publishDate;
    /**
    * 生效日期
    */
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date effectiveDate;

    private  Integer articleOrder;
    /**
    * 创建时间
    */
    private LocalDateTime createTime;
    /**
    * 更新时间
    */
    private LocalDateTime updateTime;


}
