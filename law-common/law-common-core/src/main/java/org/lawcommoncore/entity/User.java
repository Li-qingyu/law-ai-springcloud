package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.format.annotation.DateTimeFormat;

import java.io.Serializable;
import java.time.LocalDateTime;

/**
* 用户表
* @TableName user
*/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class User implements Serializable {

    /**
    * 主键ID
    */
    private Integer id;
    /**
    * 用户名
    */
    private String username;
    /**
    * 密码（加密存储）
    */
    private String password;
    /**
    * 昵称
    */
    private String nickname;
    /**
    * 邮箱
    */
    private String email;
    /**
    * 手机号
    */
    private String phone;
    /**
    * 角色：1-管理员，0-普通用户
    */
    private Integer role;
    /**
    * 状态：1-启用，0-禁用
    */
    private Integer status;
    /**
    * 创建时间
    */
    //    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createTime;

    //    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updateTime;
}
