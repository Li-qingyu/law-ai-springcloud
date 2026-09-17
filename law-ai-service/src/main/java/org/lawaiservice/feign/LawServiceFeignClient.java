package org.lawaiservice.feign;

import org.lawcommoncore.dto.LawArticlesDTO;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.result.Result;
import org.lawcommoncore.vo.LawCaseVO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.*;

@FeignClient(value = "law-law-service")
public interface LawServiceFeignClient {

    /**
     * 根据ID获取法律条文
     */
    @GetMapping("/internal/law-articles/{id}")
    Result<LawArticle> getLawArticle(@PathVariable("id") Long id);

    /**
     * 根据ID和类型ID获取案例卡片
     */
    @GetMapping("/internal/cases/card")
    Result<LawCaseVO> getLawCaseCard(@RequestParam("id") Long id);

    // ── MCP 工具链路(携带用户凭证头,下游 admin 接口 @RequireRole 生效)──
    // 日期等复杂参数以显式 @RequestParam 传递,结构体在 ServiceFeignFallback 或工具层组包

    @GetMapping("/admin/law-articles")
    Result<?> listLawArticles(@RequestParam(value = "lawBookId", required = false) Integer lawBookId,
                              @RequestParam(value = "articleTitle", required = false) String articleTitle,
                              @RequestParam(value = "page", required = false) Integer page,
                              @RequestParam(value = "pageSize", required = false) Integer pageSize);

    @PostMapping("/admin/law-articles")
    Result<?> addLawArticle(@RequestBody LawArticlesDTO dto);

    @PutMapping("/admin/law-articles/{id}")
    Result<?> updateLawArticle(@PathVariable("id") Long id,
                               @RequestParam("articleTitle") String articleTitle,
                               @RequestParam("content") String content,
                               @RequestParam(value = "lawBookId", required = false) Integer lawBookId,
                               @RequestParam(value = "bookTitle", required = false) String bookTitle,
                               @RequestParam(value = "publishDate", required = false) String publishDate,
                               @RequestParam(value = "effectiveDate", required = false) String effectiveDate,
                               @RequestParam(value = "articleOrder", required = false) Integer articleOrder);

    @DeleteMapping("/admin/law-articles/{ids}")
    Result<?> deleteLawArticles(@PathVariable("ids") java.util.List<Long> ids);

    @PostMapping("/admin/law-articles/import")
    Result<?> importLawArticles(@RequestParam("lawBookId") Integer lawBookId);

    @PostMapping("/admin/law-articles/sync")
    Result<?> syncLawArticles(@RequestParam("lawBookId") Integer lawBookId);

    @GetMapping("/admin/law-articles/sync/status")
    Result<?> syncLawArticlesStatus(@RequestParam("taskId") String taskId);

    @GetMapping("/admin/law-articles/count")
    Result<?> countLawArticles();

    @GetMapping("/admin/case")
    Result<?> listLawCases(@RequestParam(value = "title", required = false) String title,
                           @RequestParam(value = "typeId", required = false) Long typeId,
                           @RequestParam(value = "tags", required = false) String tags,
                           @RequestParam(value = "status", required = false) Integer status,
                           @RequestParam(value = "page", required = false) Integer page,
                           @RequestParam(value = "pageSize", required = false) Integer pageSize);

    @PostMapping("/admin/case")
    Result<?> addLawCase(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.dto.LawCaseDTO dto);

    @PutMapping("/admin/case")
    Result<?> updateLawCase(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.dto.LawCaseDTO dto);

    @DeleteMapping("/admin/case/{id}")
    Result<?> deleteLawCase(@PathVariable("id") Long id);

    @PostMapping("/admin/case/sync")
    Result<?> syncLawCases();

    @GetMapping("/admin/case/sync/status")
    Result<?> syncLawCasesStatus(@RequestParam("taskId") String taskId);

    @GetMapping("/admin/case/count")
    Result<?> countLawCases();

    @GetMapping("/admin/law-books")
    Result<?> listLawBooks(@RequestParam(value = "name", required = false) String name,
                           @RequestParam(value = "page", required = false) Integer page,
                           @RequestParam(value = "pageSize", required = false) Integer pageSize);

    @GetMapping("/admin/law-books/all")
    Result<?> getAllLawBooks();

    @PostMapping("/admin/law-books")
    Result<?> addLawBook(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.entity.LawBook lawBook);

    @PutMapping("/admin/law-books")
    Result<?> updateLawBook(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.entity.LawBook lawBook);

    @DeleteMapping("/admin/law-books/{ids}")
    Result<?> deleteLawBooks(@PathVariable("ids") java.util.List<Long> ids);

    @GetMapping("/admin/types/list")
    Result<?> listLawTypes(@RequestParam(value = "name", required = false) String name);

    @GetMapping("/admin/types/all")
    Result<?> getAllLawTypes();

    @PostMapping("/admin/types")
    Result<?> addLawType(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.dto.TypeDTO dto);

    @PutMapping("/admin/types")
    Result<?> updateLawType(@org.springframework.web.bind.annotation.RequestBody org.lawcommoncore.dto.TypeDTO dto);

    @DeleteMapping("/admin/types/{id}")
    Result<?> deleteLawType(@PathVariable("id") Long id);

    @GetMapping("/admin/types/count")
    Result<?> countLawTypes();
}
