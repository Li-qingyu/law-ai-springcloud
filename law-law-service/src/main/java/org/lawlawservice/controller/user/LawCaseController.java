package org.lawlawservice.controller.user;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawCaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Slf4j
@RestController("UserLawCaseController")
@RequestMapping("/user/case")
public class LawCaseController {
    @Autowired
    private LawCaseService lawCaseService;

    /**
     * 分页查询
     */
    @GetMapping
    public Result<PageResult> queryByPage(LawCasePageDTO lawCasePageDTO){
        log.info("分页查询案例{}",lawCasePageDTO);
        PageResult pageResult = lawCaseService.queryByPage(lawCasePageDTO);
        return Result.success(pageResult);
    }
    /**
     * 根据id查询
     */
    @GetMapping("/{id}")
    public Result<LawCase> get(@PathVariable Long id) {
        log.info("查询案例:{}", id);
        LawCase lawCase = lawCaseService.get(id);
        return Result.success(lawCase);
    }

}
