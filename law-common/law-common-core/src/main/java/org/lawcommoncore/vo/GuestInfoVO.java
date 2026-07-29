package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;

@AllArgsConstructor
@NoArgsConstructor
@Data
public class GuestInfoVO implements Serializable {
    private Integer guestId;
    private String guestKey;
    private Integer questionCount;
    private Integer maxQuestion;
}
