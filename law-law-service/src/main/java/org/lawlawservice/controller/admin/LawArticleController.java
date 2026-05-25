package org.lawlawservice.controller.admin;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.LawArticlesDTO;
import org.lawcommoncore.dto.LawArticlesPageDTO;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawArticleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;

@RestController
@Slf4j
@RequestMapping("/admin/law-articles")
public class LawArticleController {
    @Autowired
    private LawArticleService lawArticleService;
    @Autowired
    private StringRedisTemplate stringRedisTemplate;
    /**
     * 添加法律条文
     */
    @PostMapping
    public Result add(@RequestBody LawArticlesDTO lawArticlesDTO) {
        log.info("添加法律条文{}",lawArticlesDTO);
        lawArticleService.add(lawArticlesDTO);
        return Result.success("添加成功");
    }
    /**
     * 分页查询
     */
    @GetMapping
    public Result<PageResult> list(LawArticlesPageDTO lawArticlesPageDTO ) {
        log.info("分页查询法律条文{}",lawArticlesPageDTO);
         PageResult pageResult =lawArticleService.list(lawArticlesPageDTO);
        return Result.success(pageResult);
    }
    /**
     * 根据id查询（回显）
     */
    @GetMapping("/{id}")
    public Result<LawArticle> get(@PathVariable Long id) {
        log.info("根据id查询法律条文{}",id);
        LawArticle lawArticle = lawArticleService.get(id);
        return Result.success(lawArticle);
    }
    /**
     * 更新法律条文
     */
    @PutMapping("/{id}")
    public Result update(@PathVariable Long id, @RequestBody LawArticlesDTO lawArticlesDTO) {
        log.info("修改法律条文:{}", lawArticlesDTO);
        lawArticlesDTO.setId(id);
        lawArticleService.update(lawArticlesDTO);
        return Result.success("更新成功");
    }
    /**
     * 删除法律条文
     */
    @DeleteMapping("/{ids}")
    public Result delete(@PathVariable("ids") List< Long> ids) {
        log.info("删除法律条文:{}", ids);
        lawArticleService.delete(ids);
        return Result.success("删除成功");
    }
    /**
     * 批量导入法律条文
     */
    @PostMapping("/import")
    public Result importLawArticles(@RequestParam MultipartFile file, @RequestParam Integer lawBookId) throws IOException {
        log.info("批量导入法律条文:{},{}", file.getOriginalFilename(), lawBookId);
        String message =lawArticleService.importExcel(file, lawBookId);
        return Result.success(message);
    }
    /**
     * 查询所有法条
     */
    @GetMapping("/count")
    public Result<Integer> count() {
        log.info("查询所有法条");
        return Result.success(lawArticleService.count());
    }
    /**
     * 异步批量导入法条到milvus
     */
    @GetMapping("/sync")
    public Result importLawArticlesAsync(@RequestParam Integer lawBookId) {
        log.info("同步知识库：批量导入法条到milvus:{}", lawBookId);
         String taskId =lawArticleService.addLawArticlesToMilvusAsync(lawBookId);
        return Result.success(taskId);
    }
    @GetMapping("/sync/status")
    public Result getSyncProgress(@RequestParam String taskId) {
        String status = stringRedisTemplate.opsForValue().get("milvus_task:" + taskId);
        if (status == null) {
            return Result.error("任务不存在或已过期");
        }
        return Result.success(status);
    }



}
