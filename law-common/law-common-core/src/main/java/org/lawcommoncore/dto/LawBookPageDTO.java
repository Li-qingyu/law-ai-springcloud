package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class LawBookPageDTO implements Serializable {
    private String name;
    private Integer page;
    private Integer pageSize;
}
