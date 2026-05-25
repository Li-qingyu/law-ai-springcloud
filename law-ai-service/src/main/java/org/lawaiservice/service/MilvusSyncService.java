package org.lawaiservice.service;


import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.entity.LawCase;

import java.util.List;

public interface MilvusSyncService {
    public void addLawArticle(LawArticle article);
    public void addLawCase(LawCase lawCase) ;
    public void addConsultHistory(AiConsultation consultation);

    public void deleteLawArticle(List<Long> ids);
    public void deleteLawCase(List<Long> ids);
    public void deleteAiConsultation(List<Long> ids);

    public void addLawArticles(List<LawArticle> articles);
    public void addLawCases(List<LawCase> lawCases);
}
