package org.lawaiservice.client;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class AiConsultResponse {
    private String session_id;
    private String answer;
    private Integer turn_number;
    private List<Object> data_cards;
    private Integer user_id;
    private Map<String, Object> token_usage;
}
