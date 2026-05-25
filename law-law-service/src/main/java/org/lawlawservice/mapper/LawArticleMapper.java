package org.lawlawservice.mapper;

import com.github.pagehelper.Page;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.lawcommoncore.dto.LawArticlesPageDTO;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.vo.SearchResultVO;

import java.util.List;

@Mapper
public interface LawArticleMapper {
    void insert(LawArticle lawArticle);

    Page<LawArticle> list(LawArticlesPageDTO lawArticlesPageDTO);

    LawArticle get(Long id);

    void update(LawArticle lawArticle);

    void delete(List<Long> ids);

    int queryByBookIdCount(Long id);
    @Select("select count(1) from law_article")
    Integer count();
    @Select("select count(*) from law_article where create_time < DATE_SUB(NOW(),  INTERVAL 7 DAY)")
    Integer countOneWeekAgo();

    /**
     * 搜索法律条文
     * @param keyword 关键词
     * @return 搜索结果列表
     */
    Page<SearchResultVO> searchArticleByKeyword(@Param("keyword") String keyword);

    List<LawArticle> queryByBook(Integer bookId);
}
