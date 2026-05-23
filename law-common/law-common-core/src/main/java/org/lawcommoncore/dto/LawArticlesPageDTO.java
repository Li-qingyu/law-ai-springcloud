package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
//法律条文分页参数 数据传输对象
@Data
@AllArgsConstructor
@NoArgsConstructor
public class LawArticlesPageDTO implements Serializable {
    private Integer lawBookId;
    private String articleTitle;
    private Integer page;
    private Integer pageSize;

}
