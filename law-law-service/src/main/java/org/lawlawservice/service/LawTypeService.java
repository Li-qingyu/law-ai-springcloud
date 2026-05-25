package org.lawlawservice.service;


import org.lawcommoncore.dto.TypeDTO;
import org.lawcommoncore.entity.LawType;
import org.lawcommoncore.vo.LawTypeListVO;

import java.util.List;

public interface LawTypeService {
    LawType get(Long id);

    List<LawTypeListVO> list(String name);

    void add(TypeDTO typeDTO);

    void updateLawType(TypeDTO typeDTO);

    void delete(Long id);

    List<LawType> list();

    Integer count();
}
