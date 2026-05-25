package org.lawlawservice.service;

import org.lawcommoncore.dto.LawArticlesDTO;
import org.lawcommoncore.dto.LawArticlesPageDTO;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.PageResult;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

public interface LawArticleService {
    void add(LawArticlesDTO lawArticlesDTO);

    PageResult list(LawArticlesPageDTO lawArticlesPageDTO);

    LawArticle get(Long id);

    void update(LawArticlesDTO lawArticlesDTO);

    void delete(List<Long> ids);

    String importExcel(MultipartFile file, Integer bookId);
    Integer count();

    String addLawArticlesToMilvusAsync(Integer lawBookId);

}
