package org.lawaiservice.controller;

import org.lawaiservice.service.MilvusSyncService;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.Result;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/ai/milvus")
public class MilvusSyncController {

    @Autowired
    private MilvusSyncService milvusSyncService;

    // ==================== 法律条文 ====================

    @PostMapping("/law-article")
    public Result addLawArticle(@RequestBody LawArticle article) {
        milvusSyncService.addLawArticle(article);
        return Result.success("同步法律条文成功");
    }

    @PostMapping("/law-articles")
    public Result addLawArticles(@RequestBody List<LawArticle> articles) {
        milvusSyncService.addLawArticles(articles);
        return Result.success("批量同步法律条文成功");
    }

    @DeleteMapping("/law-articles")
    public Result deleteLawArticles(@RequestBody List<Long> ids) {
        milvusSyncService.deleteLawArticle(ids);
        return Result.success("删除法律条文成功");
    }

    // ==================== 法律案例 ====================

    @PostMapping("/law-case")
    public Result addLawCase(@RequestBody LawCase lawCase) {
        milvusSyncService.addLawCase(lawCase);
        return Result.success("同步案例成功");
    }

    @PostMapping("/law-cases")
    public Result addLawCases(@RequestBody List<LawCase> lawCases) {
        milvusSyncService.addLawCases(lawCases);
        return Result.success("批量同步案例成功");
    }

    @DeleteMapping("/law-cases")
    public Result deleteLawCases(@RequestBody List<Long> ids) {
        milvusSyncService.deleteLawCase(ids);
        return Result.success("删除案例成功");
    }

    // ==================== 咨询历史 ====================

    @PostMapping("/consult-history")
    public Result addConsultHistory(@RequestBody AiConsultation consultation) {
        milvusSyncService.addConsultHistory(consultation);
        return Result.success("同步咨询历史成功");
    }

    @DeleteMapping("/consult-history")
    public Result deleteConsultHistory(@RequestBody List<String> sessionIds) {
        milvusSyncService.deleteAiConsultation(sessionIds);
        return Result.success("删除咨询历史成功");
    }
}
