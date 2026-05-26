package org.lawlawservice.controller.admin;

import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.dto.TypeDTO;
import org.lawcommoncore.entity.LawType;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LawTypeListVO;
import org.lawlawservice.service.LawTypeService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@Slf4j
@RequestMapping("/admin/types")
public class LawTypeController {
    @Autowired
    private LawTypeService lawTypeService;
    private TypeDTO typeDTO;

    /**
     * 根据id查询类型
     */
    @GetMapping("/{id}")
    public Result<LawType> get(@PathVariable Long id) {
        log.info("查询类型:{}", id);
        LawType lawType = lawTypeService.get(id);
        return Result.success(lawType);
    }
    /**
     * 查询所有法律类型
     */
    @GetMapping("/all")
    public Result<List<LawType>> getAll() {
        log.info("查询所有法律类型");
        return Result.success(lawTypeService.list());
    }

    /**
     * 查询类型
     */
    @GetMapping("/list")
    public Result<List<LawTypeListVO>> list(@RequestParam(value ="name",required = false) String name) {
        log.info("查询所有法律类型");
        return Result.success(lawTypeService.list(name));
    }

    /**
     * 添加法律类型
     */
    @PostMapping
    public Result add(@RequestBody TypeDTO typeDTO) {
        log.info("添加法律类型:{}", typeDTO);
        lawTypeService.add(typeDTO);
        return Result.success();
    }

    /**
     * 更新法律类型
     */
    @PutMapping()
    public Result upDateLawType(@RequestBody TypeDTO typeDTO) {
        log.info("更新法律类型:{}", typeDTO);
        lawTypeService.updateLawType(typeDTO);
        return Result.success();
    }
    /**
     * 删除法律类型
     */
    @DeleteMapping("/{id}")
    public Result delete(@PathVariable Long id) {
        log.info("删除法律类型:{}", id);
        lawTypeService.delete(id);
        return Result.success();
    }
    /**
     * 统计法律类型条数
     */
    @GetMapping("/count")
    public Result<Integer> count() {
        log.info("统计法律类型条数");
        return Result.success(lawTypeService.count());
    }
    @GetMapping("/countOneWeekAgo")
    public Result<Integer> countOneWeekAgo() {
        log.info("统计一周前法律类型条数");
        return Result.success(lawTypeService.countOneWeekAgo());
    }
}
