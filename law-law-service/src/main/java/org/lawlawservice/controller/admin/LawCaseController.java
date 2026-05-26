package org.lawlawservice.controller.admin;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.LawCaseDTO;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.LawCaseStatusDTO;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawCaseService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping("/admin/case")
public class LawCaseController {
    @Autowired
    private LawCaseService lawCaseService;
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 添加案例
     */
    @PostMapping
    public Result addCase(@RequestBody LawCaseDTO lawCaseDTO) {
        log.info("添加案例:{}", lawCaseDTO.getTitle());
        lawCaseService.save(lawCaseDTO);
        return Result.success();
    }
    /**
     * 分页查询案例
     */
    @GetMapping
    public Result<PageResult> queryByPage(LawCasePageDTO lawCasePageDTO){
        log.info("分页查询案例{}",lawCasePageDTO);
        PageResult pageResult = lawCaseService.queryByPage(lawCasePageDTO);
        return Result.success(pageResult);
    }
    /**
     * 根据id查询案例
     */
    @GetMapping("/{id}")
    public Result<LawCase> get(@PathVariable Long id) {
        log.info("查询案例:{}", id);
        LawCase lawCase = lawCaseService.get(id);
        return Result.success(lawCase);
    }
    /**
     * 修改案例
     */
    @PutMapping()
    public Result update(@RequestBody LawCaseDTO lawCaseDTO) {
        log.info("修改案例:{}", lawCaseDTO.getTitle());
        lawCaseService.update(lawCaseDTO);
        return Result.success("更新成功");
    }
    /**
     * 删除案例
     */
    @DeleteMapping("/{id}")
    public Result delete(@PathVariable Long id) {
        log.info("删除案例:{}", id);
        lawCaseService.delete(id);
        return Result.success("删除成功");
    }
    /**
     * 批量管理上下架
     */
    @PutMapping("/batch-toggle-status")
    public Result batchToggleStatus(@RequestBody LawCaseStatusDTO lawCaseStatusDTO) {
        log.info("批量管理上下架:{}", lawCaseStatusDTO);
        lawCaseService.batchToggleStatus(lawCaseStatusDTO);
        return Result.success("更新成功");
    }
    /**
     * 查询案例数量（总计）
     */
    @GetMapping("/count")
    public Result<Integer>count(){
        log.info("查询案例数量");
        return Result.success(lawCaseService.count());
    }
    @GetMapping("/countOneWeekAgo")
    public Result<Integer> countOneWeekAgo(){
        log.info("查询一周前案例数量");
        return Result.success(lawCaseService.countOneWeekAgo());
    }
    /**
     * 批量同步法律案例
     *
     */
    @PostMapping("/sync")
    public Result<String> sync() {
        log.info("批量同步法律案例");
        String taskId = lawCaseService.addLawCaseToMilvusAsync();
        return Result.success(taskId);
    }
    /**
     * 查询任务状态
     */
    @GetMapping("/sync/status")
    public Result<String> getSyncStatus(@RequestParam String taskId) {
        log.info("查询任务状态:{}", taskId);
        String status =stringRedisTemplate.opsForValue().get("milvus_task:" + taskId);
        if(status == null){
            return Result.success("任务不存在或已过期");
        }
        return Result.success(status);

    }
}
