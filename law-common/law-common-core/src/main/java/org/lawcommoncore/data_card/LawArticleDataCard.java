package org.lawcommoncore.data_card;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.lawcommoncore.entity.LawArticle;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class LawArticleDataCard {
    private String type;
    private LawArticle lawArticle;
    private Float relevance;

}
