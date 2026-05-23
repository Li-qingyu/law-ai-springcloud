package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
@AllArgsConstructor
@NoArgsConstructor
@Data
public class LoginVO implements Serializable {
    private Integer id;
    private String username;
    private String name;
    private Integer status;
    private String token;
    private Integer role;
}
