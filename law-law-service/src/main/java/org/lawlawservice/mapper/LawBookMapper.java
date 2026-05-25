package org.lawlawservice.mapper;

import com.github.pagehelper.Page;
import org.apache.ibatis.annotations.Mapper;
import org.lawcommoncore.entity.LawBook;

import java.util.List;

@Mapper
public interface LawBookMapper {
    LawBook queryById(Long id);

    List<LawBook> list();

    Page<LawBook> queryByPage(String name);

    /**
     * 插入法律书
     * @param lawBook 法律书信息
     */
    void insert(LawBook lawBook);

    /**
     * 更新法律书
     * @param lawBook 法律书信息
     */
    void update(LawBook lawBook);

    /**
     * 删除法律书
     * @param ids 法律书 ID
     */
    void delete(List<Long> ids);
}
