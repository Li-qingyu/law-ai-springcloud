package org.lawaiservice.mcp.tools;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.lawcommoncore.context.BaseContext;
import org.lawcommoncore.dto.LawArticlesDTO;
import org.lawcommoncore.dto.LawArticlesPageDTO;
import org.lawcommoncore.dto.LawBookPageDTO;
import org.lawcommoncore.dto.LawCaseDTO;
import org.lawcommoncore.dto.LawCasePageDTO;
import org.lawcommoncore.dto.TypeDTO;
import org.lawcommoncore.entity.LawBook;
import org.lawcommoncore.exception.AuthorizationException;
import org.lawcommoncore.result.Result;
import org.lawcommonsecurity.constant.UserRole;
import org.lawaiservice.feign.LawServiceFeignClient;
import org.lawaiservice.mcp.registry.McpToolRegistry;
import org.springaicommunity.mcp.annotation.McpTool;
import org.springaicommunity.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Component;

import java.util.List;
import java.util.Map;

/**
 * 法律数据管理 MCP 工具(data_management 四表全量,操作清单对齐 DATA_TYPE_OPERATIONS)
 * <p>鉴权链:请求经 JwtTokenInterceptor 校验(填 BaseContext)→ 注册表权限校验(isAllowed)→
 * Feign 凭证转发(X-User-Id/X-User-Role)→ law-law-service 管理端接口(@RequireRole 生效)。</p>
 * <p>返回值统一为 Result 壳 {code,msg,data},由 MCP 框架序列化给 LLM。</p>
 */
@Slf4j
@RequiredArgsConstructor
@Component
public class LawDataMcpTools {

    private final LawServiceFeignClient lawServiceFeignClient;
    private final McpToolRegistry mcpToolRegistry;

    /** 权限校验统一入口 */
    private void assertAllowed(String toolName) {
        UserRole role = UserRole.of(BaseContext.getCurrentRole());
        if (!mcpToolRegistry.isAllowed(toolName, role)) {
            throw new AuthorizationException("无权调用 " + toolName + ", 当前角色: " + role);
        }
    }

    // ─────────────────────────── law_article ───────────────────────────

    @McpTool(name = "law_article_query",
             description = "分页查询法条列表,可按所属书籍ID与条文标题模糊搜索。返回分页数据(法条ID、标题、内容等)。只读操作。")
    public Result<?> lawArticleQuery(
            @McpToolParam(description = "所属书籍ID(Integer, 可选)", required = false) Integer lawBookId,
            @McpToolParam(description = "条文标题关键词(String, 可选, 模糊搜索)", required = false) String articleTitle,
            @McpToolParam(description = "页码(Integer, 默认1)", required = false) Integer page,
            @McpToolParam(description = "每页条数(Integer, 默认10)", required = false) Integer pageSize) {
        assertAllowed("law_article_query");
        return lawServiceFeignClient.listLawArticles(lawBookId, articleTitle,
                page == null ? 1 : page, pageSize == null ? 10 : pageSize);
    }

    @McpTool(name = "law_article_create",
             description = "新增法律条文。需要法典ID、条文标题、条文内容、发布日期与生效日期(格式yyyy-MM-dd)。写操作。")
    public Result<?> lawArticleCreate(
            @McpToolParam(description = "所属书籍ID(Integer, 必填)", required = true) Integer lawBookId,
            @McpToolParam(description = "条文标题(String, 必填, 如'第一条')", required = true) String articleTitle,
            @McpToolParam(description = "条文内容(String, 必填)", required = true) String content,
            @McpToolParam(description = "发布日期(String, 格式yyyy-MM-dd, 必填)", required = true) String publishDate,
            @McpToolParam(description = "生效日期(String, 格式yyyy-MM-dd, 必填)", required = true) String effectiveDate,
            @McpToolParam(description = "书籍标题(String, 可选)", required = false) String bookTitle,
            @McpToolParam(description = "条文排序(Integer, 可选)", required = false) Integer articleOrder) {
        assertAllowed("law_article_create");
        LawArticlesDTO dto = new LawArticlesDTO();
        dto.setLawBookId(lawBookId);
        dto.setArticleTitle(articleTitle);
        dto.setContent(content);
        dto.setBookTitle(bookTitle);
        dto.setArticleOrder(articleOrder);
        try {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd");
            dto.setPublishDate(sdf.parse(publishDate));
            dto.setEffectiveDate(sdf.parse(effectiveDate));
        } catch (java.text.ParseException e) {
            throw new IllegalArgumentException("日期格式必须为 yyyy-MM-dd: " + e.getMessage());
        }
        return lawServiceFeignClient.addLawArticle(dto);
    }

    @McpTool(name = "law_article_update",
             description = "更新法条,需条文ID与新的标题、内容。可选更新所属书籍、日期、排序。写操作。")
    public Result<?> lawArticleUpdate(
            @McpToolParam(description = "条文ID(Long, 必填)", required = true) Long id,
            @McpToolParam(description = "条文标题(String, 必填, 更新时必须传入原标题或新标题)", required = true) String articleTitle,
            @McpToolParam(description = "条文内容(String, 必填)", required = true) String content,
            @McpToolParam(description = "所属书籍ID(Integer, 可选)", required = false) Integer lawBookId,
            @McpToolParam(description = "书籍标题(String, 可选)", required = false) String bookTitle,
            @McpToolParam(description = "发布日期(String, 格式yyyy-MM-dd, 可选)", required = false) String publishDate,
            @McpToolParam(description = "生效日期(String, 格式yyyy-MM-dd, 可选)", required = false) String effectiveDate,
            @McpToolParam(description = "条文排序(Integer, 可选)", required = false) Integer articleOrder) {
        assertAllowed("law_article_update");
        return lawServiceFeignClient.updateLawArticle(id, articleTitle, content, lawBookId, bookTitle, publishDate, effectiveDate, articleOrder);
    }

    @McpTool(name = "law_article_delete",
             description = "按ID列表批量删除法条。危险操作,请先确认目标ID。写操作。")
    public Result<?> lawArticleDelete(
            @McpToolParam(description = "条文ID列表(List[Long], 必填, 如[1,2,3])", required = true) List<Long> ids) {
        assertAllowed("law_article_delete");
        return lawServiceFeignClient.deleteLawArticles(ids);
    }

    @McpTool(name = "law_article_import",
             description = "触发法条批量导入(lawBookId 指定目标法典)。返回任务信息。写操作。")
    public Result<?> lawArticleImport(
            @McpToolParam(description = "所属书籍ID(Integer, 必填)", required = true) Integer lawBookId) {
        assertAllowed("law_article_import");
        return lawServiceFeignClient.importLawArticles(lawBookId);
    }

    @McpTool(name = "law_article_sync",
             description = "同步指定法典的法条到向量库(Milvus 重操作, 返回 taskId)。写操作。")
    public Result<?> lawArticleSync(
            @McpToolParam(description = "所属书籍ID(Integer, 必填)", required = true) Integer lawBookId) {
        assertAllowed("law_article_sync");
        return lawServiceFeignClient.syncLawArticles(lawBookId);
    }

    @McpTool(name = "law_article_sync_status",
             description = "查询法条同步任务进度。只读操作。")
    public Result<?> lawArticleSyncStatus(
            @McpToolParam(description = "任务ID(String, 必填, 由 sync 返回)", required = true) String taskId) {
        assertAllowed("law_article_sync_status");
        return lawServiceFeignClient.syncLawArticlesStatus(taskId);
    }

    @McpTool(name = "law_article_count",
             description = "统计法条总数。无入参。只读操作。")
    public Result<?> lawArticleCount() {
        assertAllowed("law_article_count");
        return lawServiceFeignClient.countLawArticles();
    }

    // ─────────────────────────── law_case ───────────────────────────

    @McpTool(name = "law_case_query",
             description = "分页查询法律案例,可按标题/类型/标签/上下架状态过滤。返回分页数据。只读操作。")
    public Result<?> lawCaseQuery(
            @McpToolParam(description = "案例标题(String, 可选, 模糊搜索)", required = false) String title,
            @McpToolParam(description = "类型ID(Long, 可选)", required = false) Long typeId,
            @McpToolParam(description = "标签(String, 可选)", required = false) String tags,
            @McpToolParam(description = "状态(Integer, 可选, 0下架/1上架)", required = false) Integer status,
            @McpToolParam(description = "页码(Integer, 默认1)", required = false) Integer page,
            @McpToolParam(description = "每页条数(Integer, 默认10)", required = false) Integer pageSize) {
        assertAllowed("law_case_query");
        return lawServiceFeignClient.listLawCases(title, typeId, tags, status,
                page == null ? 1 : page, pageSize == null ? 10 : pageSize);
    }

    @McpTool(name = "law_case_create",
             description = "新增法律案例,需要标题与内容,可附类型、标签、判决结果、封面、上下架状态。写操作。")
    public Result<?> lawCaseCreate(
            @McpToolParam(description = "案例标题(String, 必填)", required = true) String title,
            @McpToolParam(description = "案例内容(String, 必填)", required = true) String content,
            @McpToolParam(description = "类型ID(Integer, 可选)", required = false) Integer typeId,
            @McpToolParam(description = "标签(String, 可选)", required = false) String tags,
            @McpToolParam(description = "判决结果(String, 可选)", required = false) String judgment,
            @McpToolParam(description = "封面图URL(String, 可选)", required = false) String cover,
            @McpToolParam(description = "状态(Integer, 可选, 0下架/1上架)", required = false) Integer status) {
        assertAllowed("law_case_create");
        LawCaseDTO dto = new LawCaseDTO();
        dto.setTitle(title);
        dto.setContent(content);
        dto.setTypeId(typeId);
        dto.setTags(tags);
        dto.setJudgment(judgment);
        dto.setCover(cover);
        dto.setStatus(status);
        return lawServiceFeignClient.addLawCase(dto);
    }

    @McpTool(name = "law_case_update",
             description = "更新法律案例,需案例ID与新的标题、内容,可更新类型/标签/判决/封面/状态。写操作。")
    public Result<?> lawCaseUpdate(
            @McpToolParam(description = "案例ID(Long, 必填)", required = true) Long id,
            @McpToolParam(description = "案例标题(String, 必填)", required = true) String title,
            @McpToolParam(description = "案例内容(String, 必填)", required = true) String content,
            @McpToolParam(description = "类型ID(Integer, 可选)", required = false) Integer typeId,
            @McpToolParam(description = "标签(String, 可选)", required = false) String tags,
            @McpToolParam(description = "判决结果(String, 可选)", required = false) String judgment,
            @McpToolParam(description = "封面图URL(String, 可选)", required = false) String cover,
            @McpToolParam(description = "状态(Integer, 可选, 0下架/1上架)", required = false) Integer status) {
        assertAllowed("law_case_update");
        LawCaseDTO dto = new LawCaseDTO();
        dto.setId(id);
        dto.setTitle(title);
        dto.setContent(content);
        dto.setTypeId(typeId);
        dto.setTags(tags);
        dto.setJudgment(judgment);
        dto.setCover(cover);
        dto.setStatus(status);
        return lawServiceFeignClient.updateLawCase(dto);
    }

    @McpTool(name = "law_case_delete",
             description = "按ID删除法律案例。危险操作。写操作。")
    public Result<?> lawCaseDelete(
            @McpToolParam(description = "案例ID(Long, 必填)", required = true) Long id) {
        assertAllowed("law_case_delete");
        return lawServiceFeignClient.deleteLawCase(id);
    }

    @McpTool(name = "law_case_sync",
             description = "同步法律案例到向量库(Milvus, 返回 taskId)。写操作。")
    public Result<?> lawCaseSync() {
        assertAllowed("law_case_sync");
        return lawServiceFeignClient.syncLawCases();
    }

    @McpTool(name = "law_case_sync_status",
             description = "查询案例同步任务进度。只读操作。")
    public Result<?> lawCaseSyncStatus(
            @McpToolParam(description = "任务ID(String, 必填, 由 sync 返回)", required = true) String taskId) {
        assertAllowed("law_case_sync_status");
        return lawServiceFeignClient.syncLawCasesStatus(taskId);
    }

    @McpTool(name = "law_case_count",
             description = "统计法律案例总数。只读操作。")
    public Result<?> lawCaseCount() {
        assertAllowed("law_case_count");
        return lawServiceFeignClient.countLawCases();
    }

    // ─────────────────────────── law_book ───────────────────────────

    @McpTool(name = "law_book_query",
             description = "分页查询法典(法律书籍)列表,可按名称模糊搜索。只读操作。")
    public Result<?> lawBookQuery(
            @McpToolParam(description = "法典名称(String, 可选, 模糊搜索)", required = false) String name,
            @McpToolParam(description = "页码(Integer, 默认1)", required = false) Integer page,
            @McpToolParam(description = "每页条数(Integer, 默认10)", required = false) Integer pageSize) {
        assertAllowed("law_book_query");
        return lawServiceFeignClient.listLawBooks(name, page == null ? 1 : page, pageSize == null ? 10 : pageSize);
    }

    @McpTool(name = "law_book_query_all",
             description = "查询全部法典列表(不分页)。只读操作。")
    public Result<?> lawBookQueryAll() {
        assertAllowed("law_book_query_all");
        return lawServiceFeignClient.getAllLawBooks();
    }

    @McpTool(name = "law_book_create",
             description = "新增法典,需要名称、发布日期、生效日期(格式yyyy-MM-dd)。写操作。")
    public Result<?> lawBookCreate(
            @McpToolParam(description = "法典名称(String, 必填)", required = true) String name,
            @McpToolParam(description = "发布日期(String, 格式yyyy-MM-dd, 必填)", required = true) String publishDate,
            @McpToolParam(description = "生效日期(String, 格式yyyy-MM-dd, 必填)", required = true) String effectiveDate) {
        assertAllowed("law_book_create");
        LawBook lawBook = new LawBook();
        lawBook.setName(name);
        try {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd");
            lawBook.setPublishDate(sdf.parse(publishDate));
            lawBook.setEffectiveDate(sdf.parse(effectiveDate));
        } catch (java.text.ParseException e) {
            throw new IllegalArgumentException("日期格式必须为 yyyy-MM-dd: " + e.getMessage());
        }
        return lawServiceFeignClient.addLawBook(lawBook);
    }

    @McpTool(name = "law_book_update",
             description = "更新法典(按 LawBook 实体字段)。写操作。")
    public Result<?> lawBookUpdate(
            @McpToolParam(description = "法典ID(Integer, 必填)", required = true) Integer id,
            @McpToolParam(description = "法典名称(String, 必填)", required = true) String name,
            @McpToolParam(description = "发布日期(String, 格式yyyy-MM-dd, 可选)", required = false) String publishDate,
            @McpToolParam(description = "生效日期(String, 格式yyyy-MM-dd, 可选)", required = false) String effectiveDate) {
        assertAllowed("law_book_update");
        LawBook lawBook = new LawBook();
        lawBook.setId(id);
        lawBook.setName(name);
        try {
            java.text.SimpleDateFormat sdf = new java.text.SimpleDateFormat("yyyy-MM-dd");
            if (publishDate != null) {
                lawBook.setPublishDate(sdf.parse(publishDate));
            }
            if (effectiveDate != null) {
                lawBook.setEffectiveDate(sdf.parse(effectiveDate));
            }
        } catch (java.text.ParseException e) {
            throw new IllegalArgumentException("日期格式必须为 yyyy-MM-dd: " + e.getMessage());
        }
        return lawServiceFeignClient.updateLawBook(lawBook);
    }

    @McpTool(name = "law_book_delete",
             description = "按ID列表批量删除法典。危险操作。写操作。")
    public Result<?> lawBookDelete(
            @McpToolParam(description = "法典ID列表(List[Long], 必填, 如[1,2])", required = true) List<Long> ids) {
        assertAllowed("law_book_delete");
        return lawServiceFeignClient.deleteLawBooks(ids);
    }

    // ─────────────────────────── law_type ───────────────────────────

    @McpTool(name = "law_type_query",
             description = "按名称搜索法律类型列表(LawTypeListVO, 不分页)。只读操作。")
    public Result<?> lawTypeQuery(
            @McpToolParam(description = "类型名称(String, 可选, 模糊搜索)", required = false) String name) {
        assertAllowed("law_type_query");
        return lawServiceFeignClient.listLawTypes(name);
    }

    @McpTool(name = "law_type_query_all",
             description = "查询全部法律类型。只读操作。")
    public Result<?> lawTypeQueryAll() {
        assertAllowed("law_type_query_all");
        return lawServiceFeignClient.getAllLawTypes();
    }

    @McpTool(name = "law_type_create",
             description = "新增法律类型,需要名称,可附描述。写操作。")
    public Result<?> lawTypeCreate(
            @McpToolParam(description = "类型名称(String, 必填)", required = true) String name,
            @McpToolParam(description = "类型描述(String, 可选)", required = false) String description) {
        assertAllowed("law_type_create");
        TypeDTO dto = new TypeDTO();
        dto.setName(name);
        dto.setDescription(description);
        return lawServiceFeignClient.addLawType(dto);
    }

    @McpTool(name = "law_type_update",
             description = "更新法律类型(ID + 名称 + 描述)。写操作。")
    public Result<?> lawTypeUpdate(
            @McpToolParam(description = "类型ID(Integer, 必填)", required = true) Integer id,
            @McpToolParam(description = "类型名称(String, 必填)", required = true) String name,
            @McpToolParam(description = "类型描述(String, 可选)", required = false) String description) {
        assertAllowed("law_type_update");
        TypeDTO dto = new TypeDTO();
        dto.setId(id);
        dto.setName(name);
        dto.setDescription(description);
        return lawServiceFeignClient.updateLawType(dto);
    }

    @McpTool(name = "law_type_delete",
             description = "按ID删除法律类型。危险操作。写操作。")
    public Result<?> lawTypeDelete(
            @McpToolParam(description = "类型ID(Long, 必填)", required = true) Long id) {
        assertAllowed("law_type_delete");
        return lawServiceFeignClient.deleteLawType(id);
    }

    @McpTool(name = "law_type_count",
             description = "统计法律类型总数。只读操作。")
    public Result<?> lawTypeCount() {
        assertAllowed("law_type_count");
        return lawServiceFeignClient.countLawTypes();
    }
}
