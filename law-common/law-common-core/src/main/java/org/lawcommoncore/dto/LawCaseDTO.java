package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
@Data
@AllArgsConstructor
@NoArgsConstructor
public class LawCaseDTO implements Serializable {
    private Long id;
    private String title;
    private Integer typeId;
    private String tags;
    private String content;
    private String judgment;
    private String cover;
    private Integer status;
}
