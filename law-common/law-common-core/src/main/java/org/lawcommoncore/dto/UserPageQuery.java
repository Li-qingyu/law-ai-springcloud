package org.lawcommoncore.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
@Data
@AllArgsConstructor
@NoArgsConstructor
public class UserPageQuery implements Serializable {
    private String name;
    private int page;
    private int pageSize;
}
