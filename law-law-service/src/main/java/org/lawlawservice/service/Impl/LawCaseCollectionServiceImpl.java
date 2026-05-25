package org.lawlawservice.service.Impl;

import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.CaseCollectionDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawlawservice.exception.LawCaseException;
import org.lawlawservice.mapper.LawCaseCollectionMapper;
import org.lawlawservice.service.LawCaseCollectionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;

@Service
public class LawCaseCollectionServiceImpl implements LawCaseCollectionService {
    @Autowired
    private LawCaseCollectionMapper lawCaseCollectionMapper;



    @Override
    public void collection(CaseCollectionDTO caseCollectionDTO) {
        if(caseCollectionDTO.getCaseId() == null){
            throw new LawCaseException("caseId不能为空");
        }
        Integer userId = BaseContext.getCurrentId();
        caseCollectionDTO.setUserId(userId);
        caseCollectionDTO.setCreateTime(LocalDateTime.now());
        lawCaseCollectionMapper.insertCaseCollection(caseCollectionDTO);
    }

    @Override
    public void cancelCollection(Integer caseId) {
        Integer userId = BaseContext.getCurrentId();
        lawCaseCollectionMapper.cancelCollection(caseId, userId);
    }

    @Override
    public List<LawCase> queryCollection() {
        Integer userId = BaseContext.getCurrentId();
        return lawCaseCollectionMapper.queryCollection(userId);
    }
}
