package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class CaseCollectionDTO implements Serializable {
    private Integer caseId;
    private Integer userId;
    private LocalDateTime createTime;
}
