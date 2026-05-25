package org.lawlawservice.controller.user;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.LawBookPageDTO;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.SearchDTO;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawBookService;
import org.lawlawservice.service.LawCaseService;
import org.lawlawservice.service.SearchService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
@Slf4j
@RestController
@RequestMapping("/user/home")
public class HomeController {
    @Autowired
    private LawCaseService lawCaseService;
    @Autowired
    private LawBookService lawBookService;
    @Autowired
    private SearchService searchService;

    @GetMapping("/cases")
    public Result<PageResult> cases(LawCasePageDTO lawCasePageDTO) {
        log.info( "查询案例{}", lawCasePageDTO);
        return Result.success( lawCaseService.queryByPage(lawCasePageDTO));
    }

    @GetMapping("/laws")
    public Result<PageResult> laws(LawBookPageDTO lawBookPageDTO) {
        log.info( "查询法律法规{}", lawBookPageDTO);
        return Result.success( lawBookService.queryByPage(lawBookPageDTO));
    }
    @GetMapping("/search")
    public Result<PageResult> search(SearchDTO searchDTO) {
        log.info("搜索关键词: {}, 类型: {}, 页码: {}, 每页数量: {}",  searchDTO.getKeyword(), searchDTO.getType(), searchDTO.getPage(), searchDTO.getPageSize());

        try {
            PageResult result = searchService.search(searchDTO);
            return Result.success(result);
        } catch (IllegalArgumentException e) {
            return Result.error(e.getMessage());
        } catch (Exception e) {
            log.error("搜索失败", e);
            return Result.error("搜索失败，请稍后重试");
        }
    }
}
