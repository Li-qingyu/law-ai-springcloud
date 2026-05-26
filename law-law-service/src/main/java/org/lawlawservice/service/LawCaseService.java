package org.lawlawservice.service;


import org.lawcommoncore.dto.LawCaseDTO;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.LawCaseStatusDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.PageResult;

public interface LawCaseService {
    void save(LawCaseDTO lawCaseDTO);

    PageResult queryByPage(LawCasePageDTO lawCasePageDTO);

    LawCase get(Long id);

    void update( LawCaseDTO lawCaseDTO);

    void delete(Long id);

    void batchToggleStatus(LawCaseStatusDTO lawCaseStatusDTO);

    Integer count();

    Integer countOneWeekAgo();

    String addLawCaseToMilvusAsync();
}
