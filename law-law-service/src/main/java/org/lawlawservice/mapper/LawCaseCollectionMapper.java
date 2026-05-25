package org.lawlawservice.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.lawcommoncore.dto.CaseCollectionDTO;
import org.lawcommoncore.entity.LawCase;

import java.util.List;

@Mapper
public interface LawCaseCollectionMapper {
    void insertCaseCollection(CaseCollectionDTO caseCollectionDTO);

    void cancelCollection(Integer caseId, Integer userId);

    List<LawCase> queryCollection(Integer userId);
}
