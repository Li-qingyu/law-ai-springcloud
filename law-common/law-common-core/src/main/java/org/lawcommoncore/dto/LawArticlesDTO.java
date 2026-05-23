package org.lawcommoncore.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;


//法律条文DTO
@Data
@AllArgsConstructor
@NoArgsConstructor
public class LawArticlesDTO {
    private Long id;
    private Integer lawBookId;
    private String bookTitle;
    private String articleTitle;
    private String content;
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date publishDate;
    @JsonFormat(pattern = "yyyy-MM-dd", timezone = "GMT+8")
    private Date effectiveDate;
    private  Integer articleOrder;

}
