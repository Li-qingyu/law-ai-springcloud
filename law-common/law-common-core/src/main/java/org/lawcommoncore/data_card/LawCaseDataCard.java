package org.lawcommoncore.data_card;


import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.lawcommoncore.vo.LawCaseVO;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LawCaseDataCard {
    private String type;
    private LawCaseVO lawCaseVO;
    private Float relevance;

}
