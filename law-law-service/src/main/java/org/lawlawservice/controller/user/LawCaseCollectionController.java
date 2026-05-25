package org.lawlawservice.controller.user;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.CaseCollectionDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawCaseCollectionService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/user/collection")
public class LawCaseCollectionController {
    @Autowired
    private LawCaseCollectionService lawCaseCollectionService;

    /**
     * 收藏案例
     */
    @PostMapping()
    public Result collection (@RequestBody CaseCollectionDTO caseCollectionDTO){
        log.info("收藏案例:{}", caseCollectionDTO);
        lawCaseCollectionService.collection(caseCollectionDTO);
        return Result.success("收藏成功");
    }
    /**
     * 取消收藏
     */
    @DeleteMapping("/{caseId}")
    public Result cancelCollection (@PathVariable Integer caseId){
        log.info("取消收藏:{}", caseId);
        lawCaseCollectionService.cancelCollection(caseId);
        return Result.success("取消成功");
    }
    /**
     * 查询收藏案例
     */
    @GetMapping
    public Result<List<LawCase>> queryCollection(){
        log.info("查询收藏案例");
        return Result.success(lawCaseCollectionService.queryCollection());
    }


}
