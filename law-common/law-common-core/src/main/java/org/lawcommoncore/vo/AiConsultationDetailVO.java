package org.lawcommoncore.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Date;
import java.util.List;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AiConsultationDetailVO {
    private Integer id;
    private String sessionId;
    private Integer turnNumber;
    private Integer userId;
    private String question;
    private String answer;
    private List<Object> dataCards;
    private String dataCardsJson;
    private Date createTime;
}
