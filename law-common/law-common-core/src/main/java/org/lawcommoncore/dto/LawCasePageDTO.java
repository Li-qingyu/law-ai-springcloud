package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class LawCasePageDTO {
    private String title;
    private Long typeId;
    private String tags;
    private Integer page;
    private Integer status;
    private Integer pageSize;
}
