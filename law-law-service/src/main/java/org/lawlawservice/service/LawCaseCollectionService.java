package org.lawlawservice.service;


import org.lawcommoncore.dto.CaseCollectionDTO;
import org.lawcommoncore.entity.LawCase;

import java.util.List;

public interface LawCaseCollectionService {
    void collection(CaseCollectionDTO caseCollectionDTO);

    void cancelCollection(Integer caseId);

    List<LawCase> queryCollection();
}
