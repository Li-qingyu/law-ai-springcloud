package org.lawlawservice.service;


import org.lawcommoncore.dto.LawBookPageDTO;
import org.lawcommoncore.entity.LawBook;
import org.lawcommoncore.result.PageResult;

import java.util.List;

public interface LawBookService {
    LawBook queryById(Long id);

    List<LawBook> list();

    PageResult queryByPage(LawBookPageDTO lawBookPageDTO);

    /**
     * 新增法律书
     * @param lawBook 法律书信息
     */
    void add(LawBook lawBook);

    /**
     * 更新法律书
     * @param lawBook 法律书信息
     */
    void update(LawBook lawBook);

    /**
     * 删除法律书
     * @param id 法律书 ID
     */
    void delete(List<Long> id);
}
