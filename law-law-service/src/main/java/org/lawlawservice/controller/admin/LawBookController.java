package org.lawlawservice.controller.admin;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.LawBookPageDTO;
import org.lawcommoncore.entity.LawBook;
import org.lawcommoncore.result.PageResult;
import org.lawcommoncore.result.Result;
import org.lawlawservice.service.LawBookService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Slf4j
@RequestMapping("/admin/law-books")
public class LawBookController {
    @Autowired
    private LawBookService lawBookService;
    /**
     * 根据 id 获取法律书
     * @param id 法律书 ID
     * @return 法律书详情
     */
    @GetMapping("/{id}")
    public Result<LawBook> getById(@PathVariable Long id) {
        log.info("获取 id: {}", id);
        LawBook lawBook = lawBookService.queryById(id);
        return Result.success(lawBook);
    }
    /**
     * 获取所有法律书
     * @return
     */
    @GetMapping("/all")
    public Result<List<LawBook>> getAll() {
        log.info("获取所有法律书");
        return Result.success(lawBookService.list());
    }
    /**
     * 分页查询法律书
     * @param lawBookPageDTO 分页查询参数
     * @return 分页结果
     */
    @GetMapping()
    public Result<PageResult> list(LawBookPageDTO lawBookPageDTO) {
        log.info("分页查询法律书{}", lawBookPageDTO);
        PageResult pageResult = lawBookService.queryByPage(lawBookPageDTO);
        return Result.success(pageResult);
    }

    /**
     * 新增法律书
     * @param lawBook 法律书信息
     * @return 操作结果
     */
    @PostMapping
    public Result add(@RequestBody LawBook lawBook) {
        log.info("新增法律书:{}", lawBook);
        lawBookService.add(lawBook);
        return Result.success();
    }

    /**
     * 更新法律书
     * @param lawBook 法律书信息
     * @return 操作结果
     */
    @PutMapping
    public Result update(@RequestBody LawBook lawBook) {
        log.info("更新法律书:{}", lawBook);
        lawBookService.update(lawBook);
        return Result.success();
    }

    /**
     * 删除法律书
     * @param ids 法律书 ID
     * @return 操作结果
     */
    @DeleteMapping("/{ids}")
    public Result delete(@PathVariable List<Long> ids) {
        log.info("删除法律书，id:{}", ids);
        lawBookService.delete(ids);
        return Result.success();
    }
}
