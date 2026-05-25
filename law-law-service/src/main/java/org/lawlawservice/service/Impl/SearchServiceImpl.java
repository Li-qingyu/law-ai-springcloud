package org.lawlawservice.service.Impl;

import com.github.pagehelper.Page;
import com.github.pagehelper.PageHelper;
import org.lawcommoncore.dto.SearchDTO;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.vo.SearchResultVO;
import org.lawlawservice.mapper.LawArticleMapper;
import org.lawlawservice.mapper.LawBookMapper;
import org.lawlawservice.mapper.LawCaseMapper;
import org.lawlawservice.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;

@Service
public class SearchServiceImpl implements SearchService {
    @Autowired
    private LawCaseMapper lawCaseMapper;

    @Autowired
    private LawArticleMapper lawArticleMapper;

    @Autowired
    private LawBookMapper lawBookMapper;

//    @Autowired
//    private AiConsultationMapper aiConsultationMapper;

    @Override
    public PageResult search(SearchDTO searchDTO) {
        String keyword = searchDTO.getKeyword();
        String type = searchDTO.getType();
        Integer page = searchDTO.getPage();
        Integer pageSize = searchDTO.getPageSize();

        // 设置默认值
        if (page == null || page < 1) {
            page = 1;
        }
        if (pageSize == null || pageSize < 1) {
            pageSize = 9;
        }
        if (type == null || type.isEmpty()) {
            type = "all";
        }

        Page<SearchResultVO> resultPage;

        // 根据类型调用不同的搜索方法
        switch (type.toLowerCase()) {
            case "case":
                PageHelper.startPage(page, pageSize);
                resultPage = lawCaseMapper.searchCaseByKeyword(keyword);
                break;
            case "code":
                PageHelper.startPage(page, pageSize);
                resultPage = lawArticleMapper.searchArticleByKeyword(keyword);
                break;
//            case "consult":
//                PageHelper.startPage(page, pageSize);
//                resultPage = aiConsultationMapper.searchConsultationByKeyword(keyword);
//                break;
            case "all":
                // 搜索所有类型，每种类型取 pageSize 条，然后合并
                return searchAllTypes(keyword, page, pageSize);
            default:
                throw new IllegalArgumentException("不支持的搜索类型: " + type);
        }

        // 构建 PageResult
        PageResult pageResult = new PageResult();
        pageResult.setTotal(resultPage.getTotal());
        pageResult.setRecords(resultPage.getResult());
        // page、pageSize、pages 字段在PageResult中不存在，暂时注释
        // pageResult.setPage(page);
        // pageResult.setPageSize(pageSize);
        // pageResult.setPages(resultPage.getPages());

        return pageResult;
    }

    /**
     * 搜索所有类型
     */
    private PageResult searchAllTypes(String keyword, int page, int pageSize) {
        List<SearchResultVO> allResults = new ArrayList<>();

        // 搜索案例
        PageHelper.startPage(page, pageSize);
        Page<SearchResultVO> casePage = lawCaseMapper.searchCaseByKeyword(keyword);
        allResults.addAll(casePage.getResult());

        // 搜索法典条文
        PageHelper.startPage(page, pageSize);
        Page<SearchResultVO> articlePage = lawArticleMapper.searchArticleByKeyword(keyword);
        allResults.addAll(articlePage.getResult());

        //TODO 搜索咨询记录
        /*PageHelper.startPage(page, pageSize);
        Page<SearchResultVO> consultPage = aiConsultationMapper.searchConsultationByKeyword(keyword);
        allResults.addAll(consultPage.getResult());*/

        // 手动分页
        int total = allResults.size();
        int totalPages = (int) Math.ceil((double) total / pageSize);
        int startIndex = (page - 1) * pageSize;
        int endIndex = Math.min(startIndex + pageSize, total);
        if (startIndex >= total) {
            PageResult emptyResult = new PageResult();
            emptyResult.setTotal(0L);
            emptyResult.setRecords(new ArrayList<>());
            return emptyResult;
        }
        List<SearchResultVO> pageData = allResults.subList(startIndex, endIndex);

        PageResult pageResult = new PageResult();
        pageResult.setTotal((long) total);
        pageResult.setRecords(pageData);
        // pageResult.setPage(page);
        // pageResult.setPageSize(pageSize);
        // pageResult.setPages(totalPages);
        return pageResult;
    }

}
