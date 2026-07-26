package org.lawuserservice.entity;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.io.Serializable;
import java.util.Date;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class GuestConsultation implements Serializable {

    private Integer id;

    private String sessionId;

    private Integer turnNumber;

    private Integer guestId;

    private String question;

    private String answer;

    private String dataCards;

    private Date createTime;
}
