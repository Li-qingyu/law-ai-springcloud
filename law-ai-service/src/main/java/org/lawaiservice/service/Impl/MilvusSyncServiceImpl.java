package org.lawaiservice.service.Impl;

import com.google.gson.Gson;
import com.google.gson.JsonArray;
import io.milvus.exception.MilvusException;
import io.milvus.v2.service.vector.request.DeleteReq;
import io.milvus.v2.service.vector.request.UpsertReq;
import io.milvus.v2.service.vector.response.UpsertResp;
import lombok.extern.slf4j.Slf4j;
import com.google.gson.JsonObject;
import org.jetbrains.annotations.NotNull;
import org.lawaiservice.exception.MilvusVectorException;
import org.lawaiservice.service.MilvusSyncService;
import org.lawcommoncore.entity.AiConsultation;
import org.lawcommoncore.entity.LawArticle;
import org.lawcommoncore.entity.LawCase;
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import com.google.common.primitives.Floats;
import io.milvus.v2.client.MilvusClientV2;

import java.util.*;


@Service
@Slf4j
public class MilvusSyncServiceImpl implements MilvusSyncService {
    @Autowired
    private MilvusClientV2 milvusClientV2;

    // 注入 EmbeddingModel 用于手动生成向量
    @Autowired
    private EmbeddingModel embeddingModel;

    /**
     * 添加法律条文 到milvus
     */
    private final Gson gson = new Gson();
    @Override
    public void addLawArticle(LawArticle article) {
        try {
            String docId = "law_article_" + article.getId();
            String text = article.getArticleTitle() + "\n" + article.getContent();
            float[] floatArray = embeddingModel.embed(text);
            List<Float> vector = Floats.asList(floatArray);

            JsonObject row = new JsonObject();
            row.addProperty("id", docId);
            row.addProperty("source_id", article.getId());
            row.addProperty("title", article.getArticleTitle());
            row.addProperty("content", truncate(article.getContent(), 1000));
            row.add("content_json", getJsonLawArticle(article));
            row.addProperty("bm25_text", buildBm25Text(article.getArticleTitle(), article.getContent()));
            row.add("vector", gson.toJsonTree(vector).getAsJsonArray());

            UpsertReq upsertReq = UpsertReq.builder()
                    .collectionName("law_articles")
                    .data(Collections.singletonList(row))
                    .build();
            milvusClientV2.upsert(upsertReq);
            log.info("成功同步法律条文到 Milvus: {}", article.getId());
        } catch (MilvusException e) {
            log.error("向量存储法律条文异常: {}", e.getMessage());
            throw new MilvusVectorException("向量存储法律条文异常");
        }
    }
    private JsonObject getJsonLawArticle(LawArticle article) {
        JsonObject json = new JsonObject();
        json.addProperty("id", article.getId());
        json.addProperty("book_id", article.getLawBookId());
        json.addProperty("article_title", article.getArticleTitle());
        json.addProperty("content", article.getContent());
        return json;
    }
    /**
     * 批量添加法律条文
     */
    @Override
    public void addLawArticles(List<LawArticle> articles) {
        List<JsonObject> rows = new ArrayList<>();
        try {
            for(LawArticle article : articles){
                String docId = "law_article_" + article.getId();
                String text = article.getArticleTitle() + "\n" + article.getContent();
                float[] floatArray = embeddingModel.embed(text);
                List<Float> vector = Floats.asList(floatArray);

                JsonObject row = new JsonObject();
                row.addProperty("id", docId);
                row.addProperty("source_id", article.getId());
                row.addProperty("title", article.getArticleTitle());
                row.addProperty("content", truncate(article.getContent(), 1000));
                row.add("content_json", getJsonLawArticle(article));
                row.addProperty("bm25_text", buildBm25Text(article.getArticleTitle(), article.getContent()));
                row.add("vector", gson.toJsonTree(vector).getAsJsonArray());
                rows.add(row);
            }
            UpsertReq upsertReq = UpsertReq.builder()
                    .collectionName("law_articles")
                    .data(rows)
                    .build();
            UpsertResp resp =milvusClientV2.upsert(upsertReq);
            log.info("成功同步法律条文 Milvus: {}",resp.getUpsertCnt()+"条");
        } catch (MilvusException e) {
            log.error("向量存储法律条文异常: {}", e.getMessage());
            throw new MilvusVectorException("向量存储法律条文异常");
        }
    }



    /**
     * 删除法律条文
     */
    @Override
    public void deleteLawArticle(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return;
        }
        // 构建 docId 列表
        String filter =buildDeleteIdsFilter(ids, "law_article_");
        DeleteReq deleteReq = DeleteReq.builder()
                .collectionName("law_articles")
                .filter(filter)
                .build();
        try {
            milvusClientV2.delete(deleteReq);
            log.info("成功删除法律条文: {}", ids);
        } catch (MilvusException e) {
            throw new MilvusVectorException( "删除法律条文异常");
        }
    }

    /**
     * 添加案例 到milvus
     */
    @Override
    public void addLawCase(LawCase lawCase) {
        try {
            String docId = "law_case_" + lawCase.getId();
            String text = lawCase.getTitle() + "\n" + lawCase.getContent();
            float[] floatArray = embeddingModel.embed(text);
            List<Float> vector = Floats.asList(floatArray);

            JsonObject row = new JsonObject();
            row.addProperty("id", docId);
            row.addProperty("source_id", lawCase.getId());
            row.addProperty("title", lawCase.getTitle());
            row.addProperty("content", truncate(lawCase.getContent(), 1000));
            row.add("content_json", getJsonLawCase(lawCase));
            row.addProperty("bm25_text", buildBm25Text(lawCase.getTitle(), lawCase.getContent()));
            // 向量
            JsonArray vectorArray = gson.toJsonTree(vector).getAsJsonArray();
            row.add("vector", vectorArray);

            UpsertReq upsertReq = UpsertReq.builder()
                    .collectionName("law_cases")
                    .data(Collections.singletonList(row))
                    .build();

            milvusClientV2.upsert(upsertReq);
            log.info("成功同步案例到 Milvus: {}", lawCase.getId());

        } catch (MilvusException e) {
            log.error("Milvus 操作失败 (案例 id={}): {}", lawCase.getId(), e.getMessage(), e);
            throw new MilvusVectorException("向量存储案例异常");
        } catch (Exception e) {
            log.error("其他异常 (案例 id={}): {}", lawCase.getId(), e.getMessage(), e);
            throw new MilvusVectorException("向量存储案例异常");
        }
    }

    @NotNull
    private static JsonObject getJsonLawCase(LawCase lawCase) {
        JsonObject json = new JsonObject();
        json.addProperty("id", lawCase.getId());
        json.addProperty("title", lawCase.getTitle());
        json.addProperty("type_id", lawCase.getTypeId());
        json.addProperty("tags", lawCase.getTags());
        json.addProperty("content", lawCase.getContent());
        json.addProperty("judgment", lawCase.getJudgment());
        json.addProperty("cover", lawCase.getCover());
        json.addProperty("publish_time", lawCase.getPublishTime() != null ? lawCase.getPublishTime().toString() : null);

        return json;
    }

    @Override
    public void addLawCases(List<LawCase> lawCases) {
        List<JsonObject> rows = new ArrayList<>();
        try {
            for(LawCase lawCase : lawCases){
                String docId = "law_case_" + lawCase.getId();
                String text = lawCase.getTitle() + "\n" + lawCase.getContent();
                float[] floatArray = embeddingModel.embed(text);
                List<Float> vector = Floats.asList(floatArray);

                JsonObject row = new JsonObject();
                row.addProperty("id", docId);
                row.addProperty("source_id", lawCase.getId());
                row.addProperty("title", lawCase.getTitle());
                row.addProperty("content", truncate(lawCase.getContent(), 1000));
                row.add("content_json", getJsonLawCase(lawCase));
                row.addProperty("bm25_text", buildBm25Text(lawCase.getTitle(), lawCase.getContent()));
                // 向量
                JsonArray vectorArray = gson.toJsonTree(vector).getAsJsonArray();
                row.add("vector", vectorArray);
                rows.add(row);
            }
            UpsertReq upsertReq = UpsertReq.builder()
                    .collectionName("law_cases")
                    .data(rows)
                    .build();

            UpsertResp resp =milvusClientV2.upsert(upsertReq);
            log.info("成功同步案例 Milvus: {}",resp.getUpsertCnt() +"条");
        } catch (MilvusException e) {
            log.info("Milvus 操作失败");
            throw new MilvusVectorException("向量存储案例异常");
        } catch (Exception e) {
            log.info("其他异常");
            throw new MilvusVectorException("向量存储案例异常");
        }
    }
    /**
     * 删除案例
     */
    @Override
    public void deleteLawCase(List<Long> ids) {
        if (ids == null || ids.isEmpty()) {
            return;
        }
        String filter = buildDeleteIdsFilter(ids, "law_case_");
        DeleteReq deleteReq = DeleteReq.builder()
                .collectionName("law_cases")
                .filter(filter)
                .build();
        try {
            milvusClientV2.delete(deleteReq);
            log.info("Milvus成功删除法律案例: {}", ids);
        } catch (MilvusException e) {
            throw new MilvusVectorException( "Milvus成功删除法律案例异常");
        }

    }


    //TODO 咨询的添加都milvus还没有实现
    /**
     * 添加咨询历史 到milvus
     */
    @Override
    public void addConsultHistory(AiConsultation consultation) {
        try {
            String docId = "consult_history_" + consultation.getId();
            String text = consultation.getQuestion() + "\n" + consultation.getAnswer();
            float[] floatArray = embeddingModel.embed(text);
            List<Float> vector = Floats.asList(floatArray);

            JsonObject row = new JsonObject();
            row.addProperty("id", docId);
            row.addProperty("source_id", Long.valueOf(consultation.getId()));
            row.addProperty("question", consultation.getQuestion());
            row.addProperty("answer", consultation.getAnswer());
            row.addProperty("session_id", consultation.getSessionId());
            row.addProperty("user_id", Long.valueOf(consultation.getUserId()));
            row.add("content_json", getJsonConsultHistory(consultation));
            row.addProperty("bm25_text", buildBm25Text(consultation.getQuestion(), consultation.getAnswer()));
            // 向量
            JsonArray vectorArray = gson.toJsonTree(vector).getAsJsonArray();
            row.add("vector", vectorArray);

            UpsertReq upsertReq = UpsertReq.builder()
                    .collectionName("consult_history")
                    .data(Collections.singletonList(row))
                    .build();

            milvusClientV2.upsert(upsertReq);
            log.info("成功同步咨询历史到 Milvus: {}", consultation.getId());

        } catch (MilvusException e) {
            log.error("Milvus 操作失败 (咨询历史 id={}): {}", consultation.getId(), e.getMessage(), e);
            throw new MilvusVectorException("向量存储咨询历史异常");
        } catch (Exception e) {
            log.error("其他异常 (咨询历史 id={}): {}", consultation.getId(), e.getMessage(), e);
            throw new MilvusVectorException("向量存储咨询历史异常");
        }
    }
    private JsonObject getJsonConsultHistory(AiConsultation consultation) {
        JsonObject json = new JsonObject();
        json.addProperty("id", consultation.getId());
        json.addProperty("question", consultation.getQuestion());
        json.addProperty("answer", consultation.getAnswer());
        json.addProperty("session_id", consultation.getSessionId());
        json.addProperty("turn_number", consultation.getTurnNumber());
        json.addProperty("user_id", consultation.getUserId());
        json.addProperty("create_time",  consultation.getCreateTime() != null ? consultation.getCreateTime().toString() : null);
        return json;
    }
    /**
     * 删除咨询历史
     */
    @Override
    public void deleteAiConsultation(List<String> sessionIds) {
        if (sessionIds == null || sessionIds.isEmpty()) {
            return ;
        }

        List<String> quotedIds = new ArrayList<>();
        for (String docId : sessionIds) {
            quotedIds.add("'" + docId + "'");
        }
        String filter = "session_id in [" + String.join(", ", quotedIds) + "]";
        DeleteReq deleteReq = DeleteReq.builder()
                .collectionName("consult_history")
                .filter(filter)
                .build();
        try {
            milvusClientV2.delete(deleteReq);
            log.info("Milvus成功删除咨询历史: {}", sessionIds);
        } catch (MilvusException e) {
            throw new MilvusVectorException( "Milvus成功删除咨询历史异常");
        }
    }




    /**
     * 验证长度是否超标
     * @param content
     * @param maxLen
     * @return
     */
    private String truncate(String content, int maxLen) {
        // 1. 空值保护：如果传入的是 null，直接返回空字符串，避免后续报错
        if (content == null) return "";

        // 2. 长度判断：如果内容长度超过了规定的 maxLen（例如 1000）
        //    就截取前 maxLen 个字符；否则原样返回
        return content.length() > maxLen ? content.substring(0, maxLen) : content;
    }

    /**
     * 构建 BM25 文本（字段加权：title/question 重复 3 次提高权重）
     */
    private String buildBm25Text(String highWeightField, String lowWeightField) {
        String high = highWeightField != null ? highWeightField : "";
        String low = lowWeightField != null ? lowWeightField : "";
        return high + " " + high + " " + high + " " + low;
    }

    /**
     *构建filter
     */
    private String buildDeleteIdsFilter(List<Long> ids,String IdName) {
        if (ids == null || ids.isEmpty()) {
            return null;
        }
        // 构建 docId 列表
        List<String> docIds = ids.stream()
                .map(id -> IdName + id)
                .toList();

        List<String> quotedIds = new ArrayList<>();
        for (String docId : docIds) {
            quotedIds.add("'" + docId + "'");
        }
        return "id in [" + String.join(", ", quotedIds) + "]";
    }

}
