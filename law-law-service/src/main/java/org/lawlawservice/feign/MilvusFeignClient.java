package org.lawlawservice.feign;

import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.entity.LawCase;
import org.lawcommoncore.result.Result;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.List;

@FeignClient(value = "law-ai-service")
public interface MilvusFeignClient {
    @PostMapping("/ai/milvus/law-article")
    Result addLawArticle(@RequestBody LawArticle article);

    @DeleteMapping("/ai/milvus/law-articles")
    Result deleteLawArticles(@RequestBody List<Long> ids);
    @PostMapping("/ai/milvus/law-articles")
    public Result addLawArticles(@RequestBody List<LawArticle> articles);

    @PostMapping("/ai/milvus/law-case")
    public Result addLawCase(@RequestBody LawCase lawCase) ;


    @PostMapping("/ai/milvus/law-cases")
    public Result addLawCases(@RequestBody List<LawCase> lawCases) ;

    @DeleteMapping("/ai/milvus/law-cases")
    public Result deleteLawCases(@RequestBody List<Long> ids) ;
}

