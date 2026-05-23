package org.lawcommoncore.data_card;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.lawcommoncore.entity.AiConsultation;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ConsultHistoryDataCard {
    private String type;
    private AiConsultation aiConsultation;
    private Float relevance;
}
