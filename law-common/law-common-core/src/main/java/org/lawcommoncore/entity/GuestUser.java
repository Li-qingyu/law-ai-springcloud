package org.lawcommoncore.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class GuestUser implements Serializable {

    private Integer id;

    private String guestKey;

    private String nickname;

    private Integer questionCount;

    private Integer maxQuestion;

    private String ipAddress;

    private String userAgent;

    private Integer isDeleted;

    private LocalDateTime deleteTime;

    private LocalDateTime createTime;

    private LocalDateTime updateTime;
}
