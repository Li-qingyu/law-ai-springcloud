package org.lawlawservice.mapper;

import com.github.pagehelper.Page;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.LawCaseStatusDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.vo.LawCaseVO;
import org.lawcommoncore.vo.SearchResultVO;

import java.util.List;

@Mapper
public interface LawCaseMapper {
    void insert(LawCase lawCase);

    Page<LawCaseVO> queryByPage(LawCasePageDTO lawCasePageDTO);

    LawCase get(Long id);

    void update(LawCase lawCase);

    void delete(Long id);

    void batchToggleStatus(LawCaseStatusDTO lawCaseStatusDTO);

    @Select("select count(*) from law_case ")
    Integer count();
    @Select("select count(*) from law_case where create_time < DATE_SUB(NOW(),  INTERVAL 7 DAY)")
    Integer countOneWeekAgo();

    /**
     * 搜索法律案例
     * @param keyword 关键词
     * @return 搜索结果列表
     */
    Page<SearchResultVO> searchCaseByKeyword(@Param("keyword") String keyword);

    List<LawCase> all();

    LawCaseVO getCard(Long id, Integer typeId);
}
